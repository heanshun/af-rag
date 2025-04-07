import requests
import json

base_url = "http://192.168.50.67:31467/api/af-liuli"


def add_config_to_center(namespaceId, environment, name, content, remark, inputtor):
    """
    向配置中心添加新配置

    参数:
        base_url (str): 配置中心API的基本URL。
        namespaceId (int): 命名空间ID。
        environment (str): 配置的环境。
        name (str): 配置名称。
        content (dict): 配置内容。
        remark (str): 配置描述。
        inputtor (str): 创建人。

    返回:
        dict: API的响应，包含状态信息或错误信息。
    """

    # 构造请求URL
    url = f"{base_url}/logic/createConfig"

    # 构造请求头，如果API需要认证信息或特定的内容类型，请在此添加
    headers = {
        'Content-Type': 'application/json'
        # 'Authorization': 'Bearer YOUR_ACCESS_TOKEN'  # 如果需要
    }

    # 构造请求体
    payload = {
        "type": "JSON",
        "namespaceId": namespaceId,
        "environment": environment,
        "name": name,
        "content": content,
        "remark": remark,
        "inputtor": inputtor
    }

    # 将字典转换为JSON格式
    data = json.dumps(payload)

    # 发送POST请求
    try:
        response = requests.post(url, headers=headers, data=data)

        # 检查是否请求成功
        response.raise_for_status()
    except requests.RequestException as e:
        # 如果发生错误，例如网络问题、无效URL、无法找到记录等，则返回错误信息。
        return {'error': str(e)}

    # 返回API的响应结果，这里是JSON格式的响应内容
    return response.json()


def Send_request(url, data):
    response = requests.post(url, data=json.dumps(data))
    print(response.status_code)
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        print("请求失败")
        return "请求失败"


def get_config_from_center(tenant_uuid, namespace_name, environment, config_name):
    """
    从配置中心获取配置信息

    参数:
        tenant_uuid (str): 租户UUID，例如 "standard"
        namespace_name (str): 命名空间名称，例如 "af-gpt-apply"
        environment (str): 配置环境，例如 "dev"
        config_name (str): 配置名称

    返回:
        dict: 配置内容，如果发生错误则返回错误信息
    """
    # 构造请求URL
    url = f"{base_url}/logic/openapi/getConfigByClient"

    # 构造请求头
    headers = {
        'Content-Type': 'application/json'
    }

    # 构造请求体
    payload = {
        "tenantUUID": tenant_uuid,
        "namespaceName": namespace_name,
        "environment": environment,
        "configName": config_name
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {'error': str(e)}
