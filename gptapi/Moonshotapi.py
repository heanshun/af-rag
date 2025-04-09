from openai import OpenAI

import knowage.logics.base as base

moonshot_key = "sk-A2FzQRwPGYy0yFNfwCBZPkP4jIgiIVlfMVCzt9mW7ToKTWhH"

api_url = "https://api.moonshot.cn/v1/chat/completions"

client = OpenAI(
    api_key=moonshot_key,
    base_url="https://api.moonshot.cn/v1"
)


def moonshot_completions(message, model="moonshot-v1-8k", history=[], max_tokens=1024, temperature=0.0):
    history += [{
        "role": "user",
        "content": message
    }]
    completion = client.chat.completions.create(
        model=model,
        messages=history,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    print(f"moonshot请求返回：\n {completion}")
    return completion.choices[0].message.content


def write_logic(demand: str, background_knowledge: str) -> str:
    """
    根据需求，利用GPT API修改业务逻辑并返回修改后内容。

    参数：
    demand：str，用户输入的需求内容。
    background_knowledge：str，背景知识。

    返回：
    str，修改后的业务逻辑内容。
    """
    logicrule = """
    logic语言是一种纯表达式语言，特点：
# logic语言说明：
1. 业务逻辑书写采用一种名叫logic的自定义语言，该语言为纯表达式语言。
2. 支持基本的表达式书写，如加减乘除，逻辑运算，字符串运算等。
3. 把赋值语句看作是一种特殊的表达式，如a = 1 + 2，其表达式结果为3，同时把a的值设置为3。
4. 支持逗号表达式，如a = 1, b = 2, c = 3，其表达式结果为3，同时把a的值设置为1，b的值设置为2，c的值设置为3。
5. 可以用小括号把表达式括起来，如(a = 1, b = 2, c = 3) + 4，其表达式结果为7，同时把a的值设置为1，b的值设置为2，c的值设置为3。
6. 支持条件表达式，如3 > 5: 1, 2。其表达式结果为2。注意，条件表达式没有if，else等关键字，其语法为：
`条件表达式: 表达式1, 表达式2`。如果条件表达式为真，则返回表达式1的结果，否则返回表达式2的结果。
7. 支持插件函数调用，如a = math.add(1, 2)，其表达式结果为3，同时把a的值设置为3。其中math为插件名，add为插件函数名。
8. 字符串只支持模版方式，其格式为：$这是{{表达式}}$，如a = $这是{{1 + 2}}$，其表达式结果为`这是3`，同时把a的值设置为3。注意：
1) 字符串内容用$$括起来。而不是用单引号或双引号。
2) 字符串中的表达式用{{}}括起来。
9. 支持json格式的字面量，如a = {{a: 1, b: 2}}，其表达式结果为`{{a: 1, b: 2}}`，同时把a的值设置为`{{a: 1, b: 2}}`。
10. 支持数组字面量，如a = [1, 2, 3]，其表达式结果为`[1, 2, 3]`，同时把a的值设置为`[1, 2, 3]`。
11. 支持数组遍历，如a = [1, 2, 3], sum = 0, a.each(sum = sum + row)。其中，row代表每一条数据。
12. 业务逻辑参数从data变量中获取，如a = data.a，其表达式结果为`data.a`，同时把a的值设置为`data.a`。
13. 用validate声明传入参数，为json格式：`validate {参数名: {required: true, default: 默认值}}`。validate语句后必须加逗号。
14. 使用 // 添加行注释。
15. 每行或者每个定义最后需要以英文逗号结尾，最后一行不用任何符号

# 常用插件：
- log，用于输出日志
  * log.debug($内容$) -> 打印debug日志
  * log.info($内容$) -> 打印info日志
  * log.warn($内容$) -> 打印warn日志
  * log.error($内容$) -> 打印error日志
- logic，用于执行业务逻辑
  * logic.run($业务逻辑名$, json格式参数) -> 执行业务逻辑并可以接收结果
- sql，用于执行 sql 操作。
  * sql.query($sql语句名$, json格式参数) -> 查询结果: 运行命名查询sql语句
  * sql.query($sql语句名$, json格式参数, $查询数量$) -> 查询结果: 运行命名查询sql语句，并指定查询数量
  * sql.query($sql语句名$, json格式参数, $查询页码$, $查询数量$) -> 查询结果: 运行命名查询sql语句，并指定查询页码和数量
  * sql.query($sql语句名$, json格式参数, $查询页码$, $查询数量$) -> 查询结果: 运行命名查询sql语句，并指定查询页码和数量
  * sql.querySQL(sql描述, $sql内容$) -> 查询结果: 运行查询sql语句
  * sql.exec($sql语句名$, json格式参数) -> 查询结果: 运行命名增删改sql语句
  * sql.execSQL($sql描述$, $sql内容$) -> 查询结果: 运行增删改sql语句
- entity，用于把 json 格式数据直接保存到数据库表中，避免调用 sql.run。
  * entity.partialSave($表名$, json格式数据) -> 把数据保存到数据库。每次只能保存一条数据。
  * entity.getById($表名$, $主键值$) -> 根据主键查询数据
- redis，用于操作redis
  * redis.set($redis键$, $值$) -> 往redis存入数据
  * redis.get($redis键$) -> 从redis获取数据
  * redis.delete($redis键$) -> 从redis删除数据
- commonTools，常用工具类
  * commonTools.getUUID() -> 生成一个带分隔字符的UUID
  * commonTools.getUUID($是否带分隔字符(boolean)$) -> 生成UUID
  * commonTools.md5($内容$) -> 对内容进行md5编码
  * commonTools.getRandomNumber($包含最小值$, $包含最大值$) -> 获取指定范围的随机数
  * commonTools.add($被加数$, $加数$) -> 加法运算
  * commonTools.sub($被减数$, $减数$) -> 减法运算
  * commonTools.mul($被乘数$, $乘数$) -> 乘法运算
  * commonTools.div($被除数$, $除数$) -> 除法运算
  * commonTools.split($内容$, $分割符$) -> 按指定分割符分割字符串，返回org.json.JSONArray格式
- dateTools，日期工具类
  * dateTools.getNow2() -> 获取当前日期字符串(格式:yyyy-MM-dd HH:mm:ss)
  * dateTools.getNow($格式$) -> 获取指定格式的当前日期字符串
  * dateTools.getNowYear() -> 获取当前年份
  * dateTools.getNowMonth() -> 获取当前月份
  * dateTools.getNowDay() -> 获取当前日
  * dateTools.format($日期$, $目标日期格式$) -> 格式化日期字符串为指定格式
  * dateTools.formatDateTime($日期$) -> 格式化日期字符串为yyyy-MM-dd HH:mm:ss格式
  * dateTools.compareDate($日期1$, $日期2$) -> 比较两个日期大小，返回boolean(日期1 > 日期2)
- restTools，http工具类
  * restTools.post($请求路径$, $请求体$) -> POST请求，返回响应字符串
  * restTools.post($请求路径$, $请求体$, $请求头$) -> POST请求，返回响应字符串
  * restTools.get($请求路径$) -> GET请求，返回响应字符串
  * restTools.get($请求路径$, $请求头$) -> GET请求，返回响应字符串
  * restTools.put($请求路径$, $请求体$) -> PUT请求，返回响应字符串
  * restTools.put($请求路径$, $请求体$, $请求头$) -> PUT请求，返回响应字符串
  * restTools.delete($请求路径$, $请求体$) -> DELETE请求，返回响应字符串
  * restTools.delete($请求路径$, $请求体$, $请求头$) -> DELETE请求，返回响应字符串
- jsonTools，json工具类
  * jsonTools.convertToJson($字符串$) -> 字符串转org.json.JSONObject
  * jsonTools.parseArray($字符串$) -> 字符串转org.json.JSONArray
  * jsonTools.readJsonFile($文件路径$) -> 读取JSON文件返回org.json.JSONObject
  * jsonTools.readJsonArrayFile($文件路径$) -> 读取JSON文件返回org.json.JSONArray
    """

    prompt = f"""{logicrule}
        根据下面需求，用logic语言写业务逻辑：
        {demand}

        需要的背景知识：
        {background_knowledge}
    """
    print(f'prompt = {prompt}')
    result = moonshot_completions(prompt, max_tokens=5000)

    return result