import importlib
import json
import logging
import time

import openai
from openai import OpenAI
import requests
from colorama import Fore, init
from requests.exceptions import Timeout

from autogpt.token_counter import count_string_tokens

# GPT API 地址
# API_URL = "http://43.156.0.111/open"
# API_URL = "https://nb.nextweb.fun/api/proxy/v1/chat/completions"
KEY = "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"

# if "HTTP_PROXY" not in os.environ and "HTTPS_PROXY" not in os.environ:
#     # 目前需要设置代理才可以访问 api
#     os.environ["HTTP_PROXY"] = "http://192.168.50.67:31691"
#     os.environ["HTTPS_PROXY"] = "http://192.168.50.67:31691"

import os

# if "HTTP_PROXY" in os.environ and "HTTPS_PROXY" in os.environ:
#     os.environ.pop("HTTP_PROXY", None)
#     os.environ.pop("HTTPS_PROXY", None)


def get_api_key():
    return KEY


def embedding(data):
    openai.api_key = KEY
    messages = data.get('messages')
    start_time = time.time()
    response = openai.Embedding.create(
        input=messages,
        model="text-embedding-ada-002"
    )
    content = response['data'][0]['embedding']
    end_time = time.time()
    # 计算请求耗时，单位为毫秒
    elapsed_time = (end_time - start_time) * 1000
    logging.info(Fore.GREEN + f"GPT获取向量开始时间：{start_time}，耗时： {elapsed_time} ms" + Fore.RESET)  # 打印绿色的结果，然后恢复正常颜色
    return content

def create_assistant(name, instructions, tools=None, model="gpt-3.5-turbo-0613", temperature=0.7):
    """
    创建一个新的Assistant

    参数:
    - name: Assistant的名称
    - instructions: Assistant的指令
    - tools: 可选，Assistant可以使用的工具列表
    - model: 可选，使用的模型，默认为"gpt-3.5-turbo-0613"
    - temperature: 可选，控制输出随机性的参数，默认为0.7

    返回:
    - 创建的Assistant对象
    """
    openai.api_key = KEY

    assistant_params = {
        "name": name,
        "instructions": instructions,
        "model": model,
        "temperature": temperature,
    }

    if tools:
        assistant_params["tools"] = tools

    try:
        assistant = openai.beta.assistants.create(**assistant_params)
        print(f"成功创建Assistant: {assistant.id}")
        return assistant
    except Exception as e:
        print(f"创建Assistant时发生错误: {str(e)}")
        return None

def use_assistant(assistant_id, user_message):
    """
    使用Assistant进行对话

    参数:
    - assistant_id: Assistant的ID
    - user_message: ��户的消息

    返回:
    - Assistant的回复
    """
    openai.api_key = KEY

    try:
        # 创建新的对话线程
        thread = openai.beta.threads.create()

        # 添加用户消息到线程
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )

        # 运行Assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # 等待运行完成
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            time.sleep(1)

        # 获取Assistant的回复
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        assistant_message = next((msg for msg in messages.data if msg.role == "assistant"), None)

        if assistant_message:
            return assistant_message.content[0].text.value
        else:
            return "Assistant没有回复。"
    except Exception as e:
        print(f"使用Assistant时发生错误: {str(e)}")
        return None

def fine_tune(file_path):
    """
    微调模型
    """
    client = openai.OpenAI(api_key = KEY)

    # 上传训练文件
    response = client.files.create(
        file=open(file_path, "rb"),
        purpose='fine-tune'
    )
    print(response)

    # 创建微调作业
    result = client.fine_tuning.jobs.create(training_file=response.id, model="gpt-4o-2024-08-06")
    return result

def list_fine_tune():
    client = openai.OpenAI(api_key = KEY)
    return client.fine_tuning.jobs.list(limit=10)

def fine_tune_status(id):
    """
    查看微调状态
    """
    client = openai.OpenAI(api_key = KEY)
    # Retrieve the state of a fine-tune
    result = client.fine_tuning.jobs.retrieve(id)
    return result


def openai_replying(data):
    client = OpenAI(
        api_key=KEY,  # this is also the default, it can be omitted
    )
    messages = data.get('messages')
    model = data.get('model', "gpt-3.5-turbo-0301")
    a = float(data.get("temperature", 0.5))
    max = int(data.get("max_tokens", 2000))
    functions = data.get("functions", [])
    function_call = data.get("function_call", "none")

    start_time = time.time()
    if len(functions) > 0:
        response = client.chat.completions.create(
            model=model,  # gpt-3.5-turbo-0301
            messages=messages,
            temperature=a,
            max_tokens=max,
            functions=functions,
            function_call=function_call,
        )
    else:
        response = client.chat.completions.create(
            model=model,  # gpt-3.5-turbo-0301
            messages=messages,
            temperature=a,
            max_tokens=max,
        )
    end_time = time.time()
    # 计算请求耗时，单位为毫秒
    elapsed_time = (end_time - start_time) * 1000
    print(Fore.GREEN + f"GPT问答请求开始时间：{start_time}，耗时： {elapsed_time} ms" + Fore.RESET)  # 打印绿色的结果，然后恢复正常颜色
    return response


def test_api(messages, max_tokens=1000, model='gpt-4o-mini-2024-07-18', temperature=0.0, functions=[],
             function_call="none"):
    # 定义请求的数据
    data = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "model": model
    }
    if len(functions) > 0:
        data["functions"] = functions
        data["function_call"] = function_call
        print(f"functions:{functions}")

    # 发送请求
    content = openai_replying(data)
    finish_reason = content.choices[0].finish_reason
    # 如果完成原因是函数调用，返回函数信息
    if finish_reason == "function_call":
        result = content.choices[0].message.function_call
        print(result.arguments)
        txt = result.arguments
        result.arguments = json.loads(txt, strict=False)
        # result["module"] =
        return finish_reason, result
    # 否则返回结果
    else:
        result = content.choices[0].message.content
        return finish_reason, result


def get_completion(prompt, max_tokens=1000, model="gpt-4o-mini-2024-07-18"):
    init()  # 初始化 colorama

    # 定义请求的数据
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "model": model,
    }
    print("GPT请求内容=========\n" + prompt)
    # 发送请求
    content = openai_replying(data)
    # 打印去掉 'choices' 后的关键信息
    # print(content)
    new_content = {k: v for k, v in content if k != 'choices'}  # 创建新的字典，去掉 'choices'
    print(Fore.GREEN + str(new_content) + Fore.RESET)  # 打印绿色的结果，然后恢复正常颜色

    print("GPT返回内容=========\n" + content.choices[0].message.content)
    print("gpt返回结束=========\n")
    return content.choices[0].message.content


def get_other(prompt):
    data = {
        "message": prompt
    }
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
    }
    parsed_data = requests.post('http://192.168.50.179:8091/gpt', data=data, headers=headers)
    print(f'get_other 返回: {parsed_data.text}')
    response = parsed_data.text.split(";")[0][1:]
    print(f'返回 ===================== {response}')
    return response


def get_llama(prompt, num_beams=0, api_url='http://192.168.50.179:8080/completion'):
    try:
        r = requests.post(
            api_url,
            json={
                "prompt": prompt,
                "n": 1,
                "use_beam_search": num_beams > 1,
                "best_of": num_beams,
                "temperature": 0,
                "stop": [";", "```", "#include", "package"],
                "max_tokens": 600,
            },
            timeout=10  # 设置超时时间为10秒
        )
        # 正常处理响应...
    except Timeout:
        print(f"请求超时，程序退出。\n{row['prompt']}\n")
        exit(1)  # 使用非零值退出，表示发生了错误

    if "[SQL]" not in prompt:
        generated_query = (
                r.json()["text"][0].split("```")[-1].split("```")[0].split(";")[0].strip()
                + ";"
        )
    else:
        generated_query = r.json()["content"]

    return generated_query


def get_llama_2(prompt, num_beams=0, api_url='http://192.168.50.179:8081/v1/chat/completions'):
    try:
        r = requests.post(
            api_url,
            json={
                "temperature": 0,
                'messages': [
                    {
                        'content': prompt,
                        'role': 'user'
                    }
                ]
            },
            timeout=10  # 设置超时时间为10秒
        )
        # 正常处理响应...
    except Timeout:
        print(f"请求超时，程序退出。\n{prompt}\n")
        exit(1)  # 使用非零值退出，表示发生了错误

    generated_query = r.json()['choices'][0]['message']['content']

    return generated_query


# 完成一轮会话
def get_chat(messages, max_tokens, gpt_model="gpt-3.5-turbo-16k-0613"):
    """完成一轮会话"""

    # 定义请求的数据
    data = {
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "model": gpt_model,
    }
    print(f"GPT请求内容=========\n{data}")
    # 发送请求
    content = openai_replying(data)

    # 打印去掉 'choices' 后的关键信息
    new_content = {k: v for k, v in content.items() if k != 'choices'}  # 创建新的字典，去掉 'choices'
    print(Fore.GREEN + str(new_content) + Fore.RESET)  # 打印绿色的结果，然后恢复正常颜色
    return content["choices"][0]["message"]["content"]


def get_answer(system_role, prompt, max_tokens=1000):
    """指定角色，获取回答。"""

    # 定义请求的数据
    data = {
        "messages": [
            {"role": "system", "content": system_role},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }
    # 发送请求
    print("GPT请求内容=========\n" + prompt)
    content = openai_replying(data)
    print("GPT返回内容=========\n" + content)
    return content


# 获取文件不超过给定tokens的内容
def get_content_with_tokens(sql_path, tokens_limit=1800):
    with open(sql_path, 'r', encoding='utf-8') as f:
        content = f.read()
    (content, tokens) = get_content_from_str(content, tokens_limit)
    return (content, tokens)


# 获取字符串不超过给定tokens的内容
def get_content_from_str(sql_str, tokens_limit):
    tokens = 0
    content = ''
    for line in sql_str.split('\n'):
        count = count_string_tokens(line, 'gpt-3.5-turbo-0301')
        if tokens + count > tokens_limit:
            break
        tokens += count
        content += line + '\n'
    return (content, tokens)


# 需求：对字符串内容进行切分，每个分片不超过给定tokens限制，返回所有分片的列表
def get_split_from_str(sql_str, tokens_limit):
    """
    :param sql_str: 待切分的字符串
    :param tokens_limit: 每个分片的最大tokens限制
    :return: 所有分片的列表
    """
    tokens = 0
    content = ''
    result = []
    for line in sql_str.split('\n'):
        count = count_string_tokens(line, 'gpt-3.5-turbo-0301')
        if tokens + count > tokens_limit:
            result.append(content)
            content = ''
            tokens = 0
        tokens += count
        content += line + '\n'
    result.append(content)
    return result


def continue_dialogue(system, demand, functions, function_module_disc, messages, function_call="auto"):
    if (len(messages) == 0):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": demand},
        ]
    elif (messages[-1]["role"] == "assistant"):
        messages.append({"role": "user", "content": demand})
    else:
        # 把messages最后一条的content改为demand
        messages[-1]["content"] = demand

    while True:
        (stop_reason, response) = test_api(messages, functions=functions, function_call=function_call)
        response_txt = bytes(str(response), "utf-8").decode("unicode_escape")
        print(Fore.GREEN + str(f"stop_reason:{stop_reason}, response:{response_txt}") + Fore.RESET)
        print(response)
        if stop_reason == "function_call":

            function_name = response.name
            function_params = response.arguments
            print(functions)

            messages.append({
                "role": 'assistant',
                "content": None,
                "function_call": {"name": function_name, "arguments": json.dumps(function_params)}
            })
            state, result = call_function(function_name, function_params, function_module_disc)
            if state == False:
                return state, messages
            messages.append({"role": "function", "name": function_name, "content": result})
        else:
            messages.append({"role": "assistant", "content": response})
            return True, messages


# 调用函数
def call_function(function_name, function_params, function_module_disc):
    module_name = function_module_disc[function_name]
    # 把moduel_name转换成'./auto/x'的形式
    module_name = module_name.replace('.', '/')
    module_name = f"./{module_name}"

    print(module_name)

    spec = importlib.util.spec_from_file_location(module_name, module_name + '.py')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # 获取函数对象并调用
    if hasattr(module, function_name):
        func = getattr(module, function_name)
        state, result = func(**function_params)
        print(state, result)
    else:
        state, result = False, f'{module_name}函数不存在'
        print('函数不存在')

    return state, result


def llama_replying(prompt, num_beams=0,max_tokens=500):
    api_url = 'http://192.168.50.179:8090/v1/chat/completions'
    try:
        r = requests.post(
            api_url,
            json={
                'messages': [
                    {
                        'content': prompt,
                        'role': 'user'
                    }
                ],
                "temperature": 0.0,
                "stop": [";"],
                "max_tokens": max_tokens,
            },
            timeout=10  # 设置超时时间为10秒
        )
        # 正常处理响应...
    except Timeout:
        print(f"请求超时，程序退出。\n{['prompt']}\n")
        exit(1)  # 使用非零值退出，表示发生了错误

    if "[SQL]" not in prompt:
        generated_query = (
                r.json()["choices"][0]["message"]["content"].split("```")[-1].split("```")[0].split(";")[0].strip()
                + ";"
        )
    else:
        generated_query = r.json()["choices"][0]["message"]["content"]

    return generated_query


def llama3_replying(prompt, history=None, max_tokens=3000, temperature=0.2):
    if history is None:
        history = []
    api_url = 'http://192.168.50.179:8091/gpt'
    try:
        r = requests.post(
            api_url,
            json={
                "prompt": prompt,
                "history": history,
                "max_tokens": max_tokens,
                "top_p": 0.0,
                "temperature": temperature,
            },
            timeout=100  # 设置超时时间为10秒
        )
        # 正常处理响应...
    except Timeout:
        print(f"请求超时，程序退出。\n{['prompt']}\n")
        exit(1)  # 使用非零值退出，表示发生了错误

    generated_query = r.text

    return generated_query


def llama3_sqlcoder(prompt,  max_tokens=128000):
    api_url = 'http://192.168.50.179:8910/v1/chat/completions'
    try:
        r = requests.post(
            api_url,
            json={
                'messages': [
                    {
                        'content': prompt,
                        'role': 'user'
                    }
                ],
                "temperature": 0.0,
                "max_tokens": max_tokens,
            },
            timeout=100  # 设置超时时间为10秒
        )
        # 正常处理响应...
    except Timeout:
        print(f"请求超时，程序退出。\n{['prompt']}\n")
        exit(1)  # 使用非零值退出，表示发生了错误

    generated_query = r.json()["choices"][0]["message"]["content"]

    return generated_query



def llama3_sqlcoder_2(prompt,  max_tokens=500):
    api_url = 'http://192.168.50.179:8091/gpt'
    try:
        r = requests.post(
            api_url,
            json={
                'message': prompt,
                "temperature": 0.0,
                "max_tokens": max_tokens,
            },
            timeout=100 # 设置超时时间为10秒
        )
        # 正常处理响应...
    except Timeout:
        print(f"请求超时，程序退出。\n{['prompt']}\n")
        exit(1)  # 使用非零值退出，表示发生了错误

    print(r.text)
    return r.text
