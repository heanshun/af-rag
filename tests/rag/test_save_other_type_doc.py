import os
from pymongo import MongoClient
from rag.trunk.markdown import convert_to_markdown, split_document, print_document_tree
from rag.trunk.save_mongo import save_doc_tree_to_mongodb, delete_document_by_name

def test_save_txt_document():
    """测试保存txt格式文档到MongoDB"""
    # 测试文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_file_path = os.path.join(current_dir, 'test_files', '测试文档2.txt')
    doc_name = "测试文档2"
    
    # 如果文档已存在，先删除
    delete_document_by_name(
        doc_name=doc_name,
        vector_space="rag_collection",
        username="admin",
        password="Class123!",
        host="localhost",
        port=27017
    )
        
    # 读取并处理文件
    with open(test_file_path, 'rb') as file:
        # 转换为markdown格式
        markdown_content = convert_to_markdown(file, 'txt')
        print("转换后的Markdown内容：")
        print(markdown_content)
        # 分割文档
        doc_tree = split_document(markdown_content)
            
    return doc_tree

if __name__ == "__main__":
    doc_tree = test_save_txt_document()
    print("文档树结构：")
    print("=" * 50)
    print_document_tree(doc_tree)
    print("=" * 50)