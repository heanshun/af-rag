import requests
from bs4 import BeautifulSoup
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def resolve_baidu_url(baidu_link):
    """将百度跳转链接还原为真实链接"""
    try:
        resp = requests.get(baidu_link, allow_redirects=True, timeout=5)
        return resp.url
    except:
        return baidu_link

def extract_web_content(url, max_length=1500):
    """提取网页正文内容，过滤乱码"""
    import re
    
    def clean_text(text):
        """清理文本，只保留中文、英文字符"""
        cleaned_chars = []
        
        for char in text:
            # 只保留中文、英文字母、数字、基本标点和空格
            if ('\u4e00' <= char <= '\u9fff' or          # 中文字符
                'a' <= char <= 'z' or                    # 英文小写
                'A' <= char <= 'Z' or                    # 英文大写
                '0' <= char <= '9' or                    # 数字
                char in ' \n\t.,!?;:()[]{}"-\''):        # 基本标点和空格
                cleaned_chars.append(char)
        
        # 合并连续的空白字符
        cleaned_text = ''.join(cleaned_chars)
        lines = cleaned_text.split('\n')
        
        # 过滤空行和过短的行
        meaningful_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 2:  # 至少3个字符才保留
                meaningful_lines.append(line)
        
        return '\n'.join(meaningful_lines)
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=8)
        
        # 尝试正确解码
        resp.encoding = resp.apparent_encoding or 'utf-8'
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 移除脚本和样式标签
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        # 清理乱码
        cleaned_text = clean_text(text)
        
        # 确保返回指定长度的有效内容
        return cleaned_text[:max_length] if cleaned_text else None
        
    except Exception as e:
        print(f"抓取失败: {url} - {e}")
        return None

def baidu_search(query, max_results=5):
    # 将中文转为URL编码
    query_encoded = urllib.parse.quote(query)
    url = f"https://www.baidu.com/s?wd={query_encoded}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"请求失败: {response.status_code}")
        return []   

    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for div in soup.find_all("div", class_="result")[:max_results]:
        a_tag = div.find("a")
        if a_tag and a_tag.get("href"):
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href")
            results.append({"title": title, "url": href})

    return results

def baidu_search_selenium(query, max_results=5):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    driver.get(f"https://www.baidu.com/s?wd={query}")
    results = []

    elements = driver.find_elements(By.CSS_SELECTOR, "h3.t > a")[:max_results]
    for el in elements:
        title = el.text
        href = el.get_attribute("href")
        results.append({"title": title, "url": href})

    driver.quit()
    return results


# ✅ 调用搜索 + 提取正文
if __name__ == "__main__":

    query = "labubu是什么"
    results = baidu_search(query, max_results=3)
    if not results: 
        print("防爬机制出现")
        results = baidu_search_selenium(query, max_results=3)
        
    for item in results:
        print(f"📌 标题: {item['title']}")
        print(f"🔗 跳转链接: {item['url']}")

        real_url = resolve_baidu_url(item["url"])
        print(f"🌐 真实链接: {real_url}")

        content = extract_web_content(real_url)
        """
        if "百度安全验证" in content:
            try:
                print("使用跳转链接，尝试提取内容")
                content = extract_web_content(item['url'])
            except Exception as e:
                print(f"跳转链接失败: {e}")
                continue
        """

        if content:
            print("📄 正文内容（前300字）:")
            print(content[:300])
        print("-" * 60)
