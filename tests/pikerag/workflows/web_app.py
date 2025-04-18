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
from rag.trunk.markdown import split_document, convert_to_markdown
from rag.trunk.api.api_json import process_api_json

app = Flask(__name__)
# 启用CORS，允许跨域请求
CORS(app, resources={r"/*": {"origins": "*"}})

# 全局变量存储当前workflow实例
current_workflow = None

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

@app.route('/api/qa/ask', methods=['POST'])
def ask():
    """提问接口"""
    if current_workflow is None:
        return jsonify({'success': False, 'message': '请先加载配置文件'})
    
    question = request.json.get('question', '').strip()
    if not question:
        return jsonify({'success': False, 'message': '问题不能为空'})
    
    try:
        qa = BaseQaData(question=question)
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
                    # 尝试从字符串中提取文档名称
                    import ast
                    chunk_dict = ast.literal_eval(chunk)
                    doc_name = chunk_dict.get('doc_name', '')
                    if doc_name:
                        references.append(doc_name)
                except:
                    continue
        
        response_data = {
            'answer': answer,
            'rationale': rationale,
            'references': references if references else ['无']
        }
        
        return jsonify({'success': True, 'data': response_data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'回答失败：{str(e)}'})

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
            supported_formats = ['pdf', 'docx', 'txt', 'xlsx', 'csv', 'md']
            if file_extension not in supported_formats:
                return jsonify({'success': False, 'message': f'不支持的文件格式：{file_extension}'})
            
            if file_extension == 'md':
                # Markdown文件直接处理
                content = file_content.decode('utf-8')
                root = split_document(content)
            else:
                # 其他格式先转换为markdown
                from io import BytesIO
                file_obj = BytesIO(file_content)
                file_obj.filename = file.filename
                content = convert_to_markdown(file_obj, file_extension)
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
        file_path = os.path.join(os.path.dirname(__file__), 'retrieved_files', doc_name)
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': f'文件不存在：{doc_name}'
            })
            
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return jsonify({
            'success': True,
            'data': {
                'name': doc_name,
                'content': content
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'读取文件失败：{str(e)}'
        })

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