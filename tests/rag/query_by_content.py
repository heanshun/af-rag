from rag.trunk.save_mongo import query_document_content

if __name__ == "__main__":
    results = query_document_content(
        "第二句话",
        username="admin",
        password="Class123!",
        host="localhost",
        port=27017,
        auth_db="admin",
        db_name="documents"
    )
    for result in results:
        print("\n找到匹配内容：")
        print(f"内容：{result['content']}")
        print(f"类型：{result['type']}")
        if result['context']['parent']:
            print(f"父节点：{result['context']['parent']['content']}")