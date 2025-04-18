from rag.trunk.save_mongo import delete_document_by_name

if __name__ == "__main__":
    # 测试删除文档（带认证信息）
    delete_success = delete_document_by_name(
        "测试文档2",
        username="admin",
        password="Class123!",
        host="localhost",
        port=27017
    )
    print(f"文档删除{'成功' if delete_success else '失败'}")