# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from typing import Any


def find_matching_brace(content: str, start_pos: int) -> int:
    """找到与给定位置的左花括号匹配的右花括号位置"""
    stack = []
    for i in range(start_pos, len(content)):
        if content[i] == '{':
            stack.append(i)
        elif content[i] == '}':
            if stack:
                stack.pop()
                if not stack:  # 找到最外层的匹配右花括号
                    return i
    return -1


def parse_json(content: str) -> Any:
    # 去除行内 // 注释
    lines = content.split('\n')
    content = '\n'.join(line.split('//')[0] for line in lines)
    content = content.replace("\n", " ")
    start_idx = content.find("{")
    if start_idx == -1:
        raise ValueError("No JSON object found")
    end_idx = find_matching_brace(content, start_idx)
    if end_idx == -1:
        raise ValueError("No matching closing brace found")
    content = content[start_idx : end_idx + 1]
    print(f"content: {content}")
    return json.loads(content)


def parse_json_v2(content: str) -> Any:
    # 去除行内 // 注释
    lines = content.split('\n')
    content = '\n'.join(line.split('//')[0] for line in lines)
    content = content.replace("\n", " ")

    start_idx = content.rfind(': "')
    end_idx = content.rfind('"}')
    if start_idx >= 0 and end_idx >= 0:
        content = content[:start_idx] + ': "' + content[start_idx + len(': "') : end_idx].replace('"', "") + '"}'

    start_idx = content.find("{")
    if start_idx == -1:
        raise ValueError("No JSON object found")
    end_idx = find_matching_brace(content, start_idx)
    if end_idx == -1:
        raise ValueError("No matching closing brace found")
    content = content[start_idx : end_idx + 1]
    print(f"content: {content}")
    return json.loads(content, strict=False)
