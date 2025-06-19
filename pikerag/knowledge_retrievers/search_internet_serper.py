import requests

def serper_search(query, api_key, max_results=5):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    data = {"q": query}
    resp = requests.post(url, json=data, headers=headers)

    if resp.status_code != 200:
        print("请求失败:", resp.status_code, resp.text)
        return []

    results = resp.json().get("organic", [])[:max_results]
    return [{"title": r["title"], "url": r["link"]} for r in results]

if __name__ == "__main__":
    api_key = "c4bd99dc01d5789a56976e14a200940070d72664"
    results = serper_search("兰州大学2025年招生简章", api_key)
    if not results:
        print("没有找到结果")
    for item in results[:5]:
        print(item["title"])
        print(item["url"])
