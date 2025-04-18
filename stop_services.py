import subprocess
import sys
import os
import psutil
import signal

def stop_flask_app():
    """停止Flask应用"""
    try:
        # 查找运行在端口5000上的进程
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.connections()
                for conn in connections:
                    if conn.laddr.port == 5000:
                        print(f"正在停止Flask应用 (PID: {proc.pid})")
                        os.kill(proc.pid, signal.SIGTERM)
                        print("Flask应用已停止")
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        print("未找到运行中的Flask应用")
    except Exception as e:
        print(f"停止Flask应用时出错: {str(e)}")

def stop_docker_containers():
    """停止所有Docker容器"""
    try:
        # 获取docker-compose.yml文件路径
        compose_file_path = os.path.join(os.path.dirname(__file__), 'docker-compose.yml')
        
        # 检查docker-compose文件是否存在
        if not os.path.exists(compose_file_path):
            print("错误: 未找到docker-compose.yml文件")
            sys.exit(1)
        
        # 停止并移除所有容器
        print("正在停止Docker容器...")
        subprocess.run(['docker-compose', '-f', compose_file_path, 'down'], check=True)
        print("Docker容器已停止并移除")
        
    except subprocess.CalledProcessError as e:
        print(f"停止Docker容器时出错: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1)

def main():
    """主函数：停止所有服务"""
    print("开始停止所有服务...")
    
    # 停止Flask应用
    stop_flask_app()
    
    # 停止Docker容器
    stop_docker_containers()
    
    print("所有服务已成功停止")

if __name__ == '__main__':
    main()