import json
import requests
import os
from openai import OpenAI
from sentence_transformers import SentenceTransformer

def get_embeddings_aliyun(message):
    # 创建1024维的零向量作为默认返回值
    default_vector = [0.0] * 1024
    
    # 如果是空字符串，返回零向量
    if not message.strip():
        print("空字符串，返回零向量")
        return default_vector
    
    # 移除代理设置（如果存在）
    if "HTTP_PROXY" in os.environ and "HTTPS_PROXY" in os.environ:
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)

    try:
        # 初始化OpenAI客户端
        client = OpenAI(
            api_key="sk-062f03efe4df47298433b72464c190ce",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # 调用embeddings API
        completion = client.embeddings.create(
            model="text-embedding-v3",
            input=message,
            dimensions=1024,
            encoding_format="float"
        )
        
        # 获取嵌入向量
        if completion and hasattr(completion, 'data') and completion.data:
            embeddings = completion.data[0].embedding
            return embeddings
        else:
            print("错误：API返回的嵌入向量为空")
            
    except Exception as e:
        print(f"调用阿里云API时发生错误: {str(e)}")

def get_embeddings_bge(message):
    """使用 BGE 模型获取文本嵌入向量
    
    Args:
        message: 需要编码的文本字符串
        
    Returns:
        numpy.ndarray: 文本的嵌入向量
    """
    # 如果是空字符串，返回零向量
    if not message.strip():
        print("空字符串，返回零向量")
        return [0.0] * 512  # BGE-small-zh 的输出维度是 512
    
    try:
        # 初始化模型
        model = SentenceTransformer('BAAI/bge-small-zh')
        
        # 获取嵌入向量
        embedding = model.encode(message, normalize_embeddings=True)
        
        # 转换为列表并返回
        return embedding.tolist()
        
    except Exception as e:
        print(f"使用BGE模型生成嵌入向量时发生错误: {str(e)}")
        # 发生错误时返回零向量
        return [0.0] * 512



