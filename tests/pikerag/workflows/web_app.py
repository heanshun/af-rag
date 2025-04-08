from flask import Flask, render_template, request, jsonify
import os
import yaml
from pikerag.workflows.qa import QaWorkflow
from pikerag.workflows.common import BaseQaData
from pikerag.utils.config_loader import load_dot_env
import importlib
import shutil

app = Flask(__name__)

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

@app.route('/')
def index():
    # 获取配置文件列表
    config_dir = os.path.join(os.path.dirname(__file__), 'configs')
    config_files = [f for f in os.listdir(config_dir) if f.endswith('.yml')]
    return render_template('index.html', config_files=config_files)

@app.route('/load_config', methods=['POST'])
def load_config():
    config_file = request.form.get('config_file')
    config_path = os.path.join(os.path.dirname(__file__), 'configs', config_file)
    
    try:
        load_workflow(config_path)
        return jsonify({'success': True, 'message': f'成功加载配置：{config_file}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'加载配置失败：{str(e)}'})

@app.route('/ask', methods=['POST'])
def ask():
    if current_workflow is None:
        return jsonify({'success': False, 'message': '请先加载配置文件'})
    
    question = request.form.get('question', '').strip()
    if not question:
        return jsonify({'success': False, 'message': '问题不能为空'})
    
    try:
        qa = BaseQaData(question=question)
        answer = current_workflow.answer(qa, 0)
        # 如果answer是字符串格式的JSON，先转换成字典
        if isinstance(answer, str):
            try:
                import json
                answer = json.loads(answer)
            except:
                pass
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        return jsonify({'success': False, 'message': f'回答失败：{str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)