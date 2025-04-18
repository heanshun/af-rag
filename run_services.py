import subprocess
import sys
import os
from tests.pikerag.workflows.web_app import app
import threading
import time

def run_docker_compose():
    """运行docker-compose启动所有容器"""
    try:
        # 假设docker-compose.yml文件在项目根目录
        compose_file_path = os.path.join(os.path.dirname(__file__), 'docker-compose.yml')
        
        # 检查docker-compose文件是否存在
        if not os.path.exists(compose_file_path):
            print("错误: 未找到docker-compose.yml文件")
            sys.exit(1)
            
        # 启动docker容器
        subprocess.run(['docker-compose', '-f', compose_file_path, 'up', '-d'], check=True)
        print("Docker容器已成功启动")
        
    except subprocess.CalledProcessError as e:
        print(f"启动Docker容器时出错: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1)

def run_flask_app():
    """运行Flask应用"""
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"启动Flask应用时出错: {str(e)}")
        sys.exit(1)

def main():
    """主函数：启动所有服务"""
    # 首先启动docker容器
    run_docker_compose()
    
    # 创建并启动Flask应用线程
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("所有服务已启动")
    print("Flask应用运行在 http://localhost:5000")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
        # 关闭docker容器
        compose_file_path = os.path.join(os.path.dirname(__file__), '../../../docker-compose.yml')
        subprocess.run(['docker-compose', '-f', compose_file_path, 'down'], check=True)
        print("服务已关闭")
        sys.exit(0)

if __name__ == '__main__':
    main()