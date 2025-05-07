import socket
import platform
import subprocess
from pymongo import MongoClient
import time

def test_port_connection(host, port):
    """
    测试端口连接
    """
    print(f"\n正在测试端口连接 {host}:{port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # 设置超时时间
    try:
        # 尝试连接
        sock.connect((host, int(port)))
        print(f"端口 {port} 开放")
        return True
    except socket.timeout:
        print(f"连接超时")
        return False
    except socket.error as e:
        print(f"连接错误: {e}")
        return False
    finally:
        sock.close()

def test_mongodb_connection():
    """
    测试 MongoDB 连接
    """
    # 尝试不同的主机配置
    configs = [
        {"host": "localhost", "port": "27017"},
        {"host": "127.0.0.1", "port": "27017"},
        {"host": "0.0.0.0", "port": "27017"}
    ]
    
    for config in configs:
        print(f"\n尝试连接配置: {config}")
        client = None
        try:
            # 尝试建立新连接
            client = MongoClient(
                host=config["host"],
                port=int(config["port"]),
                serverSelectionTimeoutMS=10000  # 10秒超时
            )
            
            # 验证连接
            server_info = client.server_info()
            print(f"连接成功! MongoDB 版本: {server_info['version']}")
            return True
            
        except Exception as e:
            print(f"连接失败: {str(e)}")
        finally:
            if client:
                client.close()
    
    return False

if __name__ == "__main__":
    # 检查 pymongo 版本
    import pymongo
    print(f"PyMongo 版本: {pymongo.__version__}")
    
    # 等待服务启动
    print("等待 MongoDB 服务启动...")
    time.sleep(10)
    
    test_mongodb_connection()