# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pikerag.prompts.base_parser import BaseContentParser
from pikerag.prompts.chunking.resplit_parser import ResplitParser
from pikerag.prompts.message_template import MessageTemplate
from pikerag.prompts.protocol import CommunicationProtocol


chunk_summary_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant good at document summarization."),
        ("user", """
# Source of the original text

The original text comes from {filename}。

# Original text

"partial original text":
{content}

# Task

Your task is to summarize the above "partial original text"

# Output

The output should contain the summary, do not add any redundant information.
""".strip()),
    ],
    input_variables=["filename", "content"],
)


chunk_summary_refinement_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant good at summary refinement."),
        ("user", """
# Source of the original text

The original text comes from {filename}。

# Original text

generalization of "partial original text":
{summary}

"partial original text":
{content}

# Task

Your task is to summarize the above "partial original text"

# Output

The output should contain the summary, do not add any redundant information.
""".strip()),
    ],
    input_variables=["filename", "summary", "content"],
)


chunk_resplit_template = MessageTemplate(
    template=[
        ("system", "You are a helpful AI assistant good at document chunking."),
        ("user", """
# Source of the original text

The original text comes from {filename}。

# Original text

generalization of "the first part" of "partial original text":
{summary}

"partial original text":
{content}

# Task

Your task:
1. Understand the generalization of "the first part" of "partial original text" and the "partial original text";
2. Analyse the structure of "partial original text", Split the "partial original text" strictly into "the first part" and "the second part", no content can be missing.
3. Provide the "end line number" of "the first part", pay attention that "the first part" is defined as: all the content of "partial original text" from Line "0" to Line "end line number" + 1, where empty is not allowed. Please note that here the maximum line number is {max_line_number}.
4. Summarize "the first part"。
5. For "the second part", considering the context and summarizing the main content of "the first part", please note that the content of "the first part" is defined as: all "partial original text" content after Line "end line number" + 1.

# Output

The output should strictly follow the format below, do not add any redundant information.

Thinking: According to the task requirements, carefully analyze the structure of the above "partial original text", think about how to reasonably split it into two parts, and output your thinking process.

<result>
<chunk>
  <endline>end line number, a non-negative number indicates the end line of "the first part". The first part will include this line.</endline>
  <summary>A summary of the "first part". Starting with "The main content of this part is". It can be referred to the generalization of "partial original text"</summary>
</chunk>
<chunk>
  <summary>Combine the context and the generalization of "the first part" to summarize the main content of "the second part". Starting with "The main content of this part is".</summary>
</chunk>
</result>
""".strip()),
    ],
    input_variables=["filename", "summary", "content", "max_line_number"],
)


chunk_summary_protocol = CommunicationProtocol(
    template=chunk_summary_template,
    parser=BaseContentParser(),
)

chunk_summary_refinement_protocol = CommunicationProtocol(
    template=chunk_summary_refinement_template,
    parser=BaseContentParser(),
)

chunk_resplit_protocol = CommunicationProtocol(
    template=chunk_resplit_template,
    parser=ResplitParser(),
)
