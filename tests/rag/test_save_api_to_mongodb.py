from rag.trunk.save_mongo import save_doc_tree_to_mongodb
from rag.trunk.api.api_json import process_api_json

if __name__ == "__main__":
    json_file_path = "rag/api_tests_json/available_apis.json"
    doc_tree = process_api_json(json_file_path)
    # 保存到MongoDB（带认证信息）
    doc_id = save_doc_tree_to_mongodb(
        doc_tree,
        "api测试文档",
        username="admin",
        password="Class123!",
        host="192.168.50.67",
        port=30429,
        auth_db="admin",
        db_name="documents"
    )
    print(f"文档已保存，ID: {doc_id}")
