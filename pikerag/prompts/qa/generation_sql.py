# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, List, Tuple

from pikerag.prompts import BaseContentParser, CommunicationProtocol, MessageTemplate
from pikerag.utils.json_parser import parse_json_v2, parse_json
import json

generation_sql_template = MessageTemplate(
    template=[
        ("system", "你是一个专业的SQL查询助手，擅长将自然语言转换为准确的SQL查询语句。"),
        ("user", """
# 任务
你的任务是根据给定的表结构和问题，生成相应的SQL查询语句。

# 数据库表结构
{context_if_any}

# 输出格式
你的输出必须严格遵循以下JSON格式：
{{
    "answer": <你生成的SQL查询语句>,
    "rationale": <SQL语句的中文解释，包括查询逻辑的说明>
}}

# 问题
{content}

让我们一步一步思考。
""".strip()),
    ],
    input_variables=["content", "context_if_any"],
)

class GenerationSqlParser(BaseContentParser):
    def encode(
        self, content: str, references: List[str]=[], context_len_limit: int=80000, **kwargs,
    ) -> Tuple[str, dict]:
        # 构建表结构上下文
        if len(references) > 0:
            context_if_any = "数据库表结构如下：\n"
            for context in list(set(references)):
                context_if_any += f"{context}\n"
                if len(context_if_any) >= context_len_limit:
                    break
        else:
            context_if_any = ""

        return content, {
            "context_if_any": context_if_any,
        }

    def decode(self, content: str, **kwargs) -> Dict[str, str]:
        try:
            output = parse_json(content)
        except Exception as e:
            print(f"[SqlParser] Content: {content}\nException: {e}")

            try:
                output = parse_json_v2(content)
            except Exception as e2:
                print(f"  [SqlParser] Exception: {e2}")

                return {
                    "answer": "parsing error",
                    "rationale": "parsing error",
                }

        for key, value in output.items():
            output[key] = str(value)
        return output


generation_sql_protocol = CommunicationProtocol(
    template=generation_sql_template,
    parser=GenerationSqlParser(),
)