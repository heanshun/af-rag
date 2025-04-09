from dataclasses import dataclass, field
from typing import List, Optional
import re

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
    # 创建根节点
    root = DocNode(content="ROOT", level=0)
    
    # 按章节分割（假设用#作为章节标记）
    chapters = re.split(r'(?m)^#\s+', doc_text)
    
    for chapter_text in chapters[1:]:  # 跳过第一个空字符串
        # 创建章节节点
        chapter_lines = chapter_text.strip().split('\n', 1)
        chapter_title = chapter_lines[0]
        chapter_node = DocNode(content=chapter_title, level=1, type="chapter")
        root.add_child(chapter_node)
        
        if len(chapter_lines) > 1:
            # 按段落分割
            paragraphs = chapter_lines[1].strip().split('\n\n')
            
            for para_text in paragraphs:
                # 创建空的段落节点
                para_node = DocNode(content="", level=2, type="paragraph")
                chapter_node.add_child(para_node)
                
                # 按标点符号分割句子
                sentences = re.split(r'([。！？；])', para_text)
                current_sentence = ""
                
                for i in range(0, len(sentences), 2):
                    if i < len(sentences):
                        current_sentence = sentences[i]
                        if i + 1 < len(sentences):
                            current_sentence += sentences[i + 1]
                        
                        if current_sentence.strip():
                            sentence_node = DocNode(content=current_sentence.strip(), level=3, type="sentence")
                            para_node.add_child(sentence_node)
    
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
    
    doc_tree = split_document(sample_text)
    print_document_tree(doc_tree)
