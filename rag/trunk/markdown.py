from dataclasses import dataclass, field
from typing import List, Optional, BinaryIO
import re
import docx
import PyPDF2
import pandas as pd
import openpyxl
from rag.trunk.convert_files import convert_to_markdown

@dataclass
class DocNode:
    """文档节点类，用于存储文档结构"""
    content: str
    level: int  # 1: 章节, 2: 段落, 3: 句子
    type: Optional[str] = None
    parent: Optional['DocNode'] = None
    children: List['DocNode'] = field(default_factory=list)
    vector_content: Optional[str] = None
    
    def add_child(self, child: 'DocNode'):
        """添加子节点"""
        child.parent = self
        self.children.append(child)

def split_document(doc_text: str) -> DocNode:
    """
    将文档按层级切分为树状结构
    返回根节点
    """
    root = DocNode(content="ROOT", level=0)
    chapters = re.split(r'(?m)^#+\s+', doc_text)
    
    for chapter_text in chapters[1:]:
        chapter_lines = chapter_text.strip().split('\n', 1)
        chapter_title = chapter_lines[0]
        chapter_node = DocNode(content=chapter_title, level=1, type="chapter")
        root.add_child(chapter_node)
        
        if len(chapter_lines) > 1:
            paragraphs = chapter_lines[1].strip().split('\n\n')
            i = 0
            while i < len(paragraphs):
                para_text = paragraphs[i].strip()
                
                # 检查是否是表格开始
                if (para_text.startswith('|') and para_text.endswith('|') and 
                    i + 1 < len(paragraphs) and 
                    paragraphs[i + 1].strip().startswith('|') and 
                    '---' in paragraphs[i + 1]):
                    
                    print("检测到表格开始")
                    # 创建表格节点
                    para_node = DocNode(content="表格", level=2, type="table")
                    chapter_node.add_child(para_node)
                    
                    # 获取表头
                    headers = [h.strip() for h in para_text.strip('|').split('|') if h.strip()]
                    
                    # 跳过分隔行
                    i += 2
                    
                    # 收集表格数据行
                    while i < len(paragraphs):
                        row_text = paragraphs[i].strip()
                        if not (row_text.startswith('|') and row_text.endswith('|')):
                            break
                            
                        cells = [c.strip() for c in row_text.strip('|').split('|') if c.strip()]
                        if cells:
                            # 检查每个单元格内容是否以标点结尾
                            processed_cells = []
                            for j in range(len(headers)):
                                if j < len(cells):
                                    cell_text = cells[j]
                                    if not cell_text[-1] in '。！？，；,.!?;':
                                        cell_text += '。'
                                    processed_cells.append(f"{headers[j]}：{cell_text}")
                            
                            row_content = ' '.join(processed_cells)
                            if row_content.strip():
                                row_node = DocNode(content=row_content, level=3, type="table_row")
                                para_node.add_child(row_node)
                        i += 1
                    continue
                
                # 处理普通段落
                para_node = DocNode(content="", level=2, type="paragraph")
                chapter_node.add_child(para_node)
                
                sentences = re.split(r'([。！？；])', para_text)
                current_sentence = ""
                for j in range(0, len(sentences), 2):
                    if j < len(sentences):
                        current_sentence = sentences[j]
                        if j + 1 < len(sentences):
                            current_sentence += sentences[j + 1]
                        
                        if current_sentence.strip():
                            sentence_node = DocNode(content=current_sentence.strip(), level=3, type="sentence")
                            para_node.add_child(sentence_node)
                i += 1
    
    return root

def print_document_tree(node: DocNode, level: int = 0):
    """打印文档树结构（用于调试）"""
    # 如果内容长度超过50，则截断并添加省略号，否则完整显示
    content_display = f"{node.content[:50]}..." if len(node.content) > 50 else node.content
    print("  " * level + f"[Level {node.level}] {content_display}")
    for child in node.children:
        print_document_tree(child, level + 1)

# 使用示例
if __name__ == "__main__":
    sample_text = """# 第一章
这是第一个段落。这是第一段的第二句话！这是第一段的第三句话。

这是第二个段落，包含一个问句？还有一个感叹句！

# 第二章
新的章节开始了。这是一段测试文本。
"""
    markdown_text = convert_to_markdown("rag/test_docs/AI信息化在华通公司的实施方案v1.1.docx", "docx")
    
    doc_tree = split_document(markdown_text)
    print_document_tree(doc_tree)
