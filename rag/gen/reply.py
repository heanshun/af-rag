from rag.search.simple import search_markdown
from gptapi.api import llama3_replying


def reply_function_simple(question, history, threshold=0.5):
    # 使用simple search替代原来的get_messages_info
    results = search_markdown(
        query=question,
        top_k=5,
        threshold=threshold,
        username="admin",
        password="Class123!",
        host="192.168.50.67",
        port=30429
    )

    # 处理列表类型的siblings，将每个siblings列表中的元素转换为字符串并连接
    message = '\n'.join(['\n'.join(map(str, item['siblings'])) for item in results])

    prompt = f"""
请根据提供的信息回答问题。

信息:
{message}

根据以上信息，回答问题：
{question}
"""

    result = llama3_replying(prompt, history=history, temperature=0.0)
    # 返回一个元组，包含响应结果和检索到的信息
    return {
        "response": result,
        "retrieved_info": results
    }


if __name__ == '__main__':
    result = reply_function_simple("感叹句在哪里？", [])
    print(result)