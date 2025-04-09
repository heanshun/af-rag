import requests
import json

token = "24.e67dec06b9af4a77cd00c3fec88a4595.2592000.1693122023.282335-36821681";
API_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant";


def get_chat(messages):

    # count = count_string_tokens(messages, 'gpt-3.5-turbo-0301')
    # max_tokens = 2000-count

    # if max_tokens < 20:
    #     print(f'''请求失败, token超限''')
    #     return f"请求失败, token超限"
    # 定义请求的数据
    data = {
        "messages": [{'role': 'user', 'content': messages}],
    }
    # 发送请求
    response = requests.post(f'{API_URL}?token={token}', json=data)
    # 检查请求是否成功
    if response.status_code == 200:
        content = json.loads(response.text)
        print(f'返回content = {content}')
        # 打印去掉 'choices' 后的关键信息
        return content['result']
    else:
        print(f'''请求失败，状态码：{response.status_code}，错误信息：{response.text}''')
        return f"请求失败, 状态码：{response.status_code}"


