from flask import Flask, jsonify, request
from flask_cors import CORS  
import os
import yaml
from pikerag.workflows.qa import QaWorkflow
from pikerag.workflows.common import BaseQaData
from pikerag.utils.config_loader import load_dot_env
import importlib
import shutil
from rag.trunk.save_mongo import delete_document_by_name
from rag.trunk.markdown import split_document
from rag.trunk.convert_files import convert_to_markdown
from rag.trunk.api.api_json import process_api_json
import ast
import json
from datetime import datetime
import hashlib

app = Flask(__name__)
# 启用CORS，允许跨域请求
CORS(app, resources={r"/*": {"origins": "*"}})

# 全局变量存储当前workflow实例
current_workflow = None

# 添加一个全局字典来存储每个会话的对话历史
chat_histories = {}
chat_archives = {}  # 存储归档的对话
ARCHIVE_PATH = os.path.join(os.path.dirname(__file__), 'chat_archives')

# 确保存档目录存在
if not os.path.exists(ARCHIVE_PATH):
    os.makedirs(ARCHIVE_PATH)

def load_workflow(config_path: str):
    """加载workflow配置"""
    global current_workflow
    
    with open(config_path, "r", encoding='utf-8') as fin:
        yaml_config = yaml.safe_load(fin)
    
    # 创建日志目录
    experiment_name = yaml_config["experiment_name"]
    log_dir = os.path.join(yaml_config["log_root_dir"], experiment_name)
    yaml_config["log_dir"] = log_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 复制配置文件到日志目录
    shutil.copy(config_path, log_dir)

    # 设置测试jsonl文件路径
    if yaml_config["test_jsonl_filename"] is None:
        yaml_config["test_jsonl_filename"] = f"{experiment_name}.jsonl"
    yaml_config["test_jsonl_path"] = os.path.join(log_dir, yaml_config["test_jsonl_filename"])

    # LLM缓存配置
    if yaml_config["llm_client"]["cache_config"]["location_prefix"] is None:
        yaml_config["llm_client"]["cache_config"]["location_prefix"] = experiment_name
    
    # 加载环境变量
    load_dot_env(env_path=yaml_config.get("dotenv_path", None))
    
    # 动态导入QA Workflow类
    workflow_module = importlib.import_module(yaml_config["workflow"]["module_path"])
    workflow_class = getattr(workflow_module, yaml_config["workflow"]["class_name"])
    assert issubclass(workflow_class, QaWorkflow)
    
    current_workflow = workflow_class(yaml_config)
    return True

@app.route('/api/configs', methods=['GET'])
def get_configs():
    """获取所有配置文件列表"""
    config_dir = os.path.join(os.path.dirname(__file__), 'configs')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    config_files = [f for f in os.listdir(config_dir) if f.endswith('.yml')]
    return jsonify({
        'success': True,
        'data': config_files
    })

@app.route('/api/config/check', methods=['POST'])
def check_config_exists():
    """检查配置文件是否存在"""
    filename = request.json.get('filename')
    if not filename:
        return jsonify({'success': False, 'message': '未提供文件名'})
    
    config_path = os.path.join(os.path.dirname(__file__), 'configs', filename)
    exists = os.path.exists(config_path)
    return jsonify({'success': True, 'exists': exists})

@app.route('/api/config/upload', methods=['POST'])
def upload_config():
    """上传配置文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'})
    
    if not file.filename.endswith('.yml'):
        return jsonify({'success': False, 'message': '只支持.yml格式的配置文件'})
    
    config_dir = os.path.join(os.path.dirname(__file__), 'configs')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    try:
        file_path = os.path.join(config_dir, file.filename)
        force_override = request.form.get('force_override', 'false').lower() == 'true'
        
        if os.path.exists(file_path) and not force_override:
            return jsonify({
                'success': False,
                'message': 'file_exists',
                'filename': file.filename
            })
        
        file.save(file_path)
        return jsonify({'success': True, 'message': f'配置文件上传成功：{file.filename}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'配置文件上传失败：{str(e)}'})

@app.route('/api/config/delete', methods=['DELETE'])
def delete_config():
    """删除配置文件"""
    filename = request.json.get('filename')
    if not filename:
        return jsonify({'success': False, 'message': '未指定要删除的配置文件'})
    
    config_path = os.path.join(os.path.dirname(__file__), 'configs', filename)
    if not os.path.exists(config_path):
        return jsonify({'success': False, 'message': f'配置文件不存在：{filename}'})
    
    try:
        os.remove(config_path)
        return jsonify({'success': True, 'message': f'配置文件删除成功：{filename}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'配置文件删除失败：{str(e)}'})

@app.route('/api/config/load', methods=['POST'])
def load_config():
    """加载配置文件"""
    filename = request.json.get('filename')
    if not filename:
        return jsonify({'success': False, 'message': '未指定配置文件'})
    
    config_path = os.path.join(os.path.dirname(__file__), 'configs', filename)
    if not os.path.exists(config_path):
        return jsonify({'success': False, 'message': f'配置文件不存在：{filename}'})
    
    try:
        load_workflow(config_path)
        return jsonify({'success': True, 'message': f'成功加载配置：{filename}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'加载配置失败：{str(e)}'})

@app.route('/api/qa/chat', methods=['POST'])
def chat():
    """对话接口"""
    if current_workflow is None:
        return jsonify({'success': False, 'message': '请先加载配置文件'})
    
    data = request.json
    question = data.get('question', '').strip()
    session_id = data.get('session_id')  # 用于标识不同的对话会话
    
    if not question:
        return jsonify({'success': False, 'message': '问题不能为空'})
    
    try:
        # 获取或创建会话历史
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        
        # 将当前问题添加到历史记录
        chat_histories[session_id].append({
            'role': 'user',
            'content': question,
            'rationale': '',  # 添加理由字段
            'references': []  # 添加参考来源字段
        })
        
        # 构建完整的上下文
        context = "\n".join([
            f"{'用户' if msg['role'] == 'user' else '助手'}: {msg['content']}"
            for msg in chat_histories[session_id]
        ])
        
        # 使用完整上下文进行回答
        qa = BaseQaData(question=context)
        result = current_workflow.answer(qa, 0)
        
        # 解析回答内容
        answer = result.get('answer', '')
        rationale = result.get('rationale', '')
        
        # 处理参考来源
        reference_chunks = result.get('reference_chunks', [])
        references = []
        if reference_chunks:
            for chunk in reference_chunks:
                try:
                    chunk_dict = ast.literal_eval(chunk)
                    doc_name = chunk_dict.get('doc_name', '')
                    if doc_name and doc_name not in references:  # 添加去重判断
                        references.append(doc_name)
                except:
                    continue
        
        # 将回答添加到历史记录，包含理由和参考来源
        chat_histories[session_id].append({
            'role': 'assistant',
            'content': answer,
            'rationale': rationale,
            'references': references if references else ['无']
        })
        
        response_data = {
            'answer': answer,
            'rationale': rationale,
            'references': references if references else ['无'],
            'history': chat_histories[session_id]  # 返回完整的对话历史
        }
        
        return jsonify({'success': True, 'data': response_data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'回答失败：{str(e)}'})

@app.route('/api/qa/history', methods=['GET'])
def get_chat_history():
    """获取对话历史"""
    session_id = request.args.get('session_id')
    if not session_id or session_id not in chat_histories:
        return jsonify({'success': True, 'data': []})
    return jsonify({'success': True, 'data': chat_histories[session_id]})

@app.route('/api/qa/clear', methods=['POST'])
def clear_chat_history():
    """清空对话历史并归档"""
    session_id = request.json.get('session_id')
    if session_id in chat_histories and chat_histories[session_id]:
        try:
            # 获取第一个用户问题作为标题
            first_question = next(msg['content'] for msg in chat_histories[session_id] if msg['role'] == 'user')
            current_history = chat_histories[session_id]
            
            # 检查是否是现有对话的延续
            existing_archive_id = None
            for filename in os.listdir(ARCHIVE_PATH):
                if not filename.endswith('.json'):
                    continue
                    
                with open(os.path.join(ARCHIVE_PATH, filename), 'r', encoding='utf-8') as f:
                    archive_data = json.load(f)
                    # 如果第一个问题相同，认为是同一个对话的延续
                    if archive_data['title'] == first_question:
                        existing_archive_id = filename[:-5]  # 移除.json后缀
                        break
            
            # 创建归档记录，确保包含理由和参考来源
            archive_data = {
                'title': first_question,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'history': current_history,  # 现在包含了理由和参考来源
                'session_id': session_id
            }
            
            if existing_archive_id:
                # 更新现有记录
                archive_id = existing_archive_id
                print(f"更新现有对话记录: {archive_id}")
            else:
                # 创建新记录
                archive_id = hashlib.md5(f"{first_question}{datetime.now()}".encode()).hexdigest()
                print(f"创建新对话记录: {archive_id}")
            
            # 保存到本地文件
            archive_file = os.path.join(ARCHIVE_PATH, f'{archive_id}.json')
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, ensure_ascii=False, indent=2)
            
            # 保存到内存中
            chat_archives[archive_id] = archive_data
            
        except Exception as e:
            print(f"归档对话失败: {str(e)}")
        
        # 清空当前会话历史
        chat_histories[session_id] = []
        
    return jsonify({'success': True, 'message': '对话历史已清空并归档'})

@app.route('/api/qa/archives', methods=['GET'])
def get_chat_archives():
    """获取所有归档的对话列表"""
    try:
        archives = []
        # 读取目录下所有归档文件
        for filename in os.listdir(ARCHIVE_PATH):
            if filename.endswith('.json'):
                with open(os.path.join(ARCHIVE_PATH, filename), 'r', encoding='utf-8') as f:
                    archive_data = json.load(f)
                    archives.append({
                        'id': filename[:-5],  # 移除.json后缀
                        'title': archive_data['title'],
                        'timestamp': archive_data['timestamp']
                    })
        return jsonify({
            'success': True,
            'data': sorted(archives, key=lambda x: x['timestamp'], reverse=True)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取归档列表失败：{str(e)}'
        })

@app.route('/api/qa/archives/<archive_id>', methods=['GET'])
def restore_chat_archive(archive_id):
    """恢复归档的对话"""
    try:
        archive_file = os.path.join(ARCHIVE_PATH, f'{archive_id}.json')
        if not os.path.exists(archive_file):
            return jsonify({
                'success': False,
                'message': '找不到指定的归档对话'
            })
            
        with open(archive_file, 'r', encoding='utf-8') as f:
            archive_data = json.load(f)
            
        # 恢复对话历史
        session_id = archive_data['session_id']
        chat_histories[session_id] = archive_data['history']
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'history': archive_data['history']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'恢复归档对话失败：{str(e)}'
        })

@app.route('/api/qa/archives/<archive_id>', methods=['DELETE'])
def delete_chat_archive(archive_id):
    """删除归档的对话"""
    try:
        archive_file = os.path.join(ARCHIVE_PATH, f'{archive_id}.json')
        if not os.path.exists(archive_file):
            return jsonify({
                'success': False,
                'message': '找不到指定的归档对话'
            })
            
        # 删除文件
        os.remove(archive_file)
        
        # 如果存在内存中的记录也删除
        if archive_id in chat_archives:
            del chat_archives[archive_id]
            
        return jsonify({
            'success': True,
            'message': '归档对话已删除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除归档对话失败：{str(e)}'
        })

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """获取所有文档列表"""
    try:
        from pymongo import MongoClient
        client = MongoClient(host="localhost", port=27017, 
                           username="admin", password="Class123!")
        db = client.documents
        # 只获取name字段
        docs = list(db.documents.find({}, {"name": 1, "_id": 0}))
        return jsonify({
            'success': True,
            'data': [doc['name'] for doc in docs]  # 直接返回名称列表
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取文档列表失败：{str(e)}'
        })

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """上传并处理文档"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'})
    
    file = request.files['file']
    doc_name = request.form.get('name', file.filename)
    force_override = request.form.get('force_override', 'false').lower() == 'true'
    
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'})
    
    try:
        # 修改为绝对路径，并打印出来以便调试
        retrieved_files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'retrieved_files')
        print(f"Trying to save file to: {retrieved_files_dir}")
        
        if not os.path.exists(retrieved_files_dir):
            os.makedirs(retrieved_files_dir)
            print(f"Created directory: {retrieved_files_dir}")
            
        # 保存文件到本地
        file_path = os.path.join(retrieved_files_dir, doc_name)
        print(f"Saving file to: {file_path}")
        
        file.save(file_path)
        
        # 验证文件是否成功保存
        if os.path.exists(file_path):
            print(f"File exists after save: {file_path}")
            print(f"File size: {os.path.getsize(file_path)} bytes")
        else:
            print(f"WARNING: File does not exist after save: {file_path}")
        
        # 检查文档是否已存在
        from pymongo import MongoClient
        client = MongoClient(host="localhost", port=27017, 
                           username="admin", password="Class123!")
        db = client.documents
        existing_doc = db.documents.find_one({"name": doc_name})
        
        if existing_doc and not force_override:
            return jsonify({
                'success': False,
                'message': 'document_exists',
                'name': doc_name,
                'needConfirm': True
            })
        
        # 如果文档存在且用户确认替换，先删除旧文档
        if existing_doc and force_override:
            delete_document_by_name(
                doc_name,
                vector_space="rag_collection",
                username="admin",
                password="Class123!",
                host="localhost",
                port=27017
            )
            # 删除本地文件（如果存在）
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # 重新打开文件以读取内容
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 根据文件扩展名处理文件
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension == 'json':
            # API JSON文件处理
            content = file_content.decode('utf-8')
            root = process_api_json(content)
        else:
            # 其他格式文件处理
            supported_formats = ['pdf', 'docx', 'txt', 'xlsx', 'html', 'htm', 'md']
            if file_extension not in supported_formats:
                return jsonify({'success': False, 'message': f'不支持的文件格式：{file_extension}'})
            
            if file_extension == 'md':
                # Markdown文件直接处理
                content = file_content.decode('utf-8')
                root = split_document(content)
            else:
                # 其他格式先转换为markdown
                content = convert_to_markdown(file_path, file_extension)
                root = split_document(content)
        
        # 保存到MongoDB
        from rag.trunk.save_mongo import save_doc_tree_to_mongodb
        doc_id = save_doc_tree_to_mongodb(
            root=root,
            doc_name=doc_name,
            vector_space="rag_collection",
            username="admin",
            password="Class123!",
            host="localhost",
            port=27017
        )
        
        # 在处理完成后再次检查文件
        if os.path.exists(file_path):
            print(f"File still exists after processing: {file_path}")
            print(f"Final file size: {os.path.getsize(file_path)} bytes")
        else:
            print(f"WARNING: File was deleted during processing: {file_path}")
        
        return jsonify({
            'success': True,
            'message': f'文档{"替换" if force_override else "上传"}成功：{doc_name}',
            'doc_id': doc_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'文档处理失败：{str(e)}'
        })

@app.route('/api/documents/delete', methods=['DELETE'])
def delete_document():
    """删除文档"""
    doc_name = request.json.get('name')
    if not doc_name:
        return jsonify({'success': False, 'message': '未指定要删除的文档'})
    
    try:
        # 删除MongoDB中的文档
        success = delete_document_by_name(
            doc_name,
            vector_space="rag_collection",
            username="admin",
            password="Class123!",
            host="localhost",
            port=27017
        )
        
        # 删除本地文件
        file_path = os.path.join(os.path.dirname(__file__), 'retrieved_files', doc_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'文档删除成功：{doc_name}'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'文档不存在：{doc_name}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'文档删除失败：{str(e)}'
        })

@app.route('/api/documents/content/<path:doc_name>', methods=['GET'])
def get_document_content(doc_name):
    """获取文档内容"""
    try:
        # 构建完整的文件路径
        file_path = os.path.join(os.path.dirname(__file__), 'retrieved_files', doc_name)
        
        # 获取文件类型
        file_type = doc_name.split('.')[-1].lower()
        
        if file_type == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif file_type == 'pdf':
            import pdfplumber
            content = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    content.append(page.extract_text())
            return '\n'.join(content)
            
        elif file_type == 'docx':
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            
        elif file_type == 'xlsx':
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_string()
            
        elif file_type in ['html', 'htm']:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                return soup.get_text()
                
        elif file_type == 'md':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
            
    except Exception as e:
        print(f"处理文件 {doc_name} 时发生错误: {str(e)}")
        return ""

@app.route('/api/documents/path/<path:doc_name>', methods=['GET'])
def get_document_path(doc_name):
    """获取文档的完整路径"""
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'retrieved_files', doc_name)
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': f'文件不存在：{doc_name}'
            })
            
        return jsonify({
            'success': True,
            'data': {
                'name': doc_name,
                'path': f'file:///{file_path.replace("\\", "/")}'  # 转换为文件协议格式
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取文件路径失败：{str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)