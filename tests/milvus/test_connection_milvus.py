import socket
import platform
import subprocess
from pymilvus import connections, utility
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

def test_milvus_connection():
    """
    测试 Milvus 连接
    """
    # 尝试不同的主机配置
    configs = [
        {"host": "localhost", "port": "19530"},
        {"host": "127.0.0.1", "port": "19530"},
        {"host": "0.0.0.0", "port": "19530"}
    ]
    
    for config in configs:
        print(f"\n尝试连接配置: {config}")
        try:
            # 确保之前的连接已断开
            try:
                connections.disconnect("default")
            except:
                pass
                
            # 尝试建立新连接
            connections.connect(
                alias="default",
                host=config["host"],
                port=config["port"],
                timeout=10,
                secure=False
            )
            
            # 验证连接
            version = utility.get_server_version()
            print(f"连接成功! Milvus 版本: {version}")
            return True
            
        except Exception as e:
            print(f"连接失败: {str(e)}")
        finally:
            try:
                connections.disconnect("default")
            except:
                pass
    
    return False

if __name__ == "__main__":
    # 检查 pymilvus 版本
    import pymilvus
    print(f"PyMilvus 版本: {pymilvus.__version__}")
    
    # 等待服务启动
    print("等待 Milvus 服务启动...")
    time.sleep(10)
    
    test_milvus_connection()