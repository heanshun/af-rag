# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pikerag.prompts.base_parser import BaseContentParser
from pikerag.prompts.chunking.resplit_parser import ResplitParser
from pikerag.prompts.message_template import MessageTemplate
from pikerag.prompts.protocol import CommunicationProtocol

# TODO: Modify these prompts to be general.

chunk_summary_template_Chinese = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant good at document summarization."),
        ("user", """
# 原文来源

原文来自 {source} 的政策文档 {filename}。

# 原文

“部分原文”：
{content}

# 任务要求

你的任务是输出以上“部分原文”的总结。

# 输出

只输出内容总结，不要添加其他任何内容。
""".strip())
    ],
    input_variables=["source", "filename", "content"],
)


chunk_summary_refinement_template_Chinese = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant good at summary refinement."),
        ("user", """
# 原文来源

原文来自 {source} 的政策文档 {filename}。

# 原文

“部分原文”的内容概括：
{summary}

“部分原文”：
{content}

# 任务要求

你的任务是输出以上“部分原文”的总结。

# 输出

只输出内容总结，不要添加其他任何内容。
""".strip()),
    ],
    input_variables=["source", "filename", "summary", "content"],
)


chunk_resplit_template_Chinese = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant good at document chunking."),
        ("user", """
# 原文来源

原文来自 {source} 的政策文档 {filename}。

# 原文

“部分原文”的“第一部分”内容概括：
{summary}

“部分原文”：
{content}

# 任务要求

你的任务:
1. 理解“部分原文”的“第一部分”的辅助信息和“部分原文”的内容。
2. 分析“部分原文”的结构，将“部分原文”严格切分为“第一部分”和“第二部分”，不允许有内容缺失。
3. 给出“第一部分”的“结束行号”，请注意，这里“第一部分”的内容定义为：从“Line 0”到“Line 结束行号 + 1”之间的全部“部分原文”内容，不允许为空。请注意，此文“最大行号”为{max_line_number}。
4. 概括“第一部分”的主要内容。
5. 对于“第二部分”，结合上下文和“第一部分”的内容概括它的主要内容，请注意，这里“第二部分”的内容定义为：从“Line 结束行号 + 1”之后的全部“部分原文”内容。

# 输出

按以下格式输出：

思考：<按照任务要求，仔细分析以上“部分原文”的结构，思考如何将它合理划分为两个部分，输出你的思考过程。>

<result>
<chunk>
  <endline>结束行号，一个非负的数字，表示“第一部分”在这一行结束。第一部分会包含这一行。</endline>
  <summary>“第一部分”的详细内容总结。以“这部分的主要内容为”开头，可以结合“部分原文”的内容概括。</summary>
</chunk>
<chunk>
  <summary>结合上下文和第一部分的内容概括第二部分的主要内容。以“这部分的主要内容为”开头。</summary>
</chunk>
</result>
""".strip()),
    ],
    input_variables=["source", "filename", "summary", "content", "max_line_number"],
)


chunk_summary_protocol_Chinese = CommunicationProtocol(
    template=chunk_summary_template_Chinese,
    parser=BaseContentParser(),
)

chunk_summary_refinement_protocol_Chinese = CommunicationProtocol(
    template=chunk_summary_refinement_template_Chinese,
    parser=BaseContentParser(),
)

chunk_resplit_protocol_Chinese = CommunicationProtocol(
    template=chunk_resplit_template_Chinese,
    parser=ResplitParser(),
)
