from rag.trunk.markdown import split_document
from rag.trunk.save_mongo import save_doc_tree_to_mongodb

# 使用示例
if __name__ == "__main__":
    # 假设我们已经有了文档树
    sample_text = """# 第一章
这是第一个段落。这是第一段的第二句话！这是第一段的第三句话。

这是第二个段落，包含一个问句？还有一个感叹句！

# 第二章
新的章节开始了。这是一段测试文本。
"""
    doc_tree = split_document(sample_text)
    
    # 保存到MongoDB（带认证信息）
    doc_id = save_doc_tree_to_mongodb(
        doc_tree,
        "测试文档",
        username="admin",
        password="Class123!",
        host="localhost",
        port=27017
    )
    print(f"文档已保存，ID: {doc_id}")
