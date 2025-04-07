from pikerag.workflows.chain_of_rag import process_reference_chunks

def test_process_reference_chunks():
    # 准备测试数据
    test_chunks = [
        """{
            'doc_id': '67eb8822edc1b85329a5ecda',
            'doc_name': 'api测试文档',
            'matched_content': "{'name': '获取用气量数据API', 'description': '获取某个时段的用气量数据。', 'endpoint': '/api/v1/users/{user_id}', 'method': 'GET', 'parameters': ['user_id']}",
            'node_type': 'api',
            'level': 1
        }""",
        """{
            'doc_id': '67eb8822edc1b85329a5ecdb',
            'doc_name': '系统文档',
            'matched_content': '系统架构设计说明文档第三章',
            'node_type': 'document',
            'level': 2
        }""",
        """{
            'doc_id': '67eb8822edc1b85329a5ecdc',
            'doc_name': 'api文档',
            'matched_content': "{'name': '获取设备状态API', 'description': '获取设备当前运行状态', 'endpoint': '/api/v1/devices/{device_id}/status', 'method': 'GET', 'parameters': ['device_id']}",
            'node_type': 'api',
            'level': 1
        }""",
        """{
            'doc_id': '67c17e4db02e8ac3a1d25a30',
            'doc_name': '售后日常工作制度',
            'matched_content': '由部门领导评估协调后安排人员处理。',
            'node_type': 'sentence',
            'level': 3,
            'siblings': ['为了营造更好的工作环境和工作氛围，现将售后日常工作做规范处理。',
                      '## 日常上下班及值班规定\\r\\n### 一、周内早晨值班\\r\\n值班人员上班时间8:00，周轮流制。',
                      '非值班人员无特殊情况需在9:00到达公司进入工作状态。',
                      '- 查看群里面的群消息，及时回应并处理。'],
            'parent': ''
        }""",
        """{
            'doc_id': '67c17e4db02e8ac3a1d25a31',
            'doc_name': '售后日常工作制度',
            'matched_content': '每日需对各自处理的燃气公司的售后情况做简单的问题登记描述。',
            'node_type': 'sentence',
            'level': 3,
            'siblings': ['### 工单登记：OA-->工作流-->工作流项目-->售后工单流程\\r\\n- 用户每日提交上来的工单，需根据问题情况处理完成或者派发分配完成。',
                      '- 持续跟踪工单登记的问题处理情况，根据情况及时做出相应调整并通知用户。',
                      '- 对不影响用户正常办理业务的问题或不能及时处理的问题，优先让用户登记工单防止遗漏。'],
            'parent': '## 日常工作规范及要求'
        }"""
    ]

    # 调用函数
    apis, documents = process_reference_chunks(test_chunks)

    # 打印结果
    print("\n=== 测试 process_reference_chunks 函数 ===")
    print("\n1. API类型的chunks:")
    for api in apis:
        print(f"  - {api}")
    
    print("\n2. Document类型的chunks:")
    for doc in documents:
        print(f"  - {doc}")

if __name__ == "__main__":
    test_process_reference_chunks() 