from dataclasses import dataclass, field
from typing import List, Optional
import json
from ..markdown import DocNode

def split_document(json_doc: dict) -> DocNode:
    """
    将JSON格式的API文档转换为树状结构
    返回一个包含API信息和description的list作为level 1
    """
    # 创建根节点
    root = DocNode(content="ROOT", level=0)
    
    # 获取available_apis的第一个API信息
    api_info = json_doc['available_apis'][0]
    node = DocNode(content=str(api_info), vector_content=str(api_info['description']), level=1, type="api")
    root.add_child(node)
    
    return root

def print_document_tree(node: DocNode, level: int = 0):
    """打印文档树结构"""
    print("  " * level + f"[Level {node.level}] {node.content} (vector_content: {node.vector_content})")
    for child in node.children:
        print_document_tree(child, level + 1)

def process_api_json(json_file_path: str) -> DocNode:
    """
    处理API JSON文件并返回文档树
    
    Args:
        json_file_path: JSON文件的路径
        
    Returns:
        DocNode: 处理后的文档树
        
    Raises:
        FileNotFoundError: 文件不存在时抛出
        json.JSONDecodeError: JSON格式错误时抛出
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            api_data = json.load(f)
            
        # 创建文档树
        doc_tree = split_document(api_data)
        return doc_tree
        
    except FileNotFoundError:
        raise FileNotFoundError(f"错误：找不到文件 {json_file_path}")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"错误：JSON文件格式不正确 {json_file_path}")

# 测试代码
if __name__ == "__main__":   
    json_file_path = "rag/api_tests_json/available_apis.json"
    doc_tree = process_api_json(json_file_path)
    print("API文档树结构：")
    print_document_tree(doc_tree)
