from dataclasses import dataclass, field
from typing import List, Optional, BinaryIO
import re
import docx
import PyPDF2
import pandas as pd
import openpyxl

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

def convert_to_markdown(file: BinaryIO, file_type: str) -> str:
    """
    将不同格式的文件转换为markdown格式
    
    Args:
        file: 文件对象
        file_type: 文件类型 ('pdf', 'docx', 'txt', 'xlsx', 'csv')
    
    Returns:
        str: 转换后的markdown文本
    """
    if file_type == 'pdf':
        # 处理PDF文件
        reader = PyPDF2.PdfReader(file)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text.strip():
                text_parts.append(text)
        return "\n\n".join(text_parts)
    
    elif file_type == 'docx':
        # 处理Word文档
        doc = docx.Document(file)
        markdown_text = []
        
        for para in doc.paragraphs:
            if para.style.name.startswith('Heading'):
                # 根据标题级别添加#号
                level = int(para.style.name[-1])
                markdown_text.append(f"{'#' * level} {para.text}")
            else:
                markdown_text.append(para.text)
        
        return "\n\n".join(markdown_text)
    
    elif file_type in ['xlsx', 'csv']:
        # 处理Excel或CSV文件
        if file_type == 'xlsx':
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        
        # 将表格转换为markdown表格格式
        markdown_table = df.to_markdown()
        return f"# 数据表格\n\n{markdown_table}"
    
    elif file_type == 'txt':
        # 处理纯文本文件
        text = file.read().decode('utf-8')
        
        # 添加文档标题
        filename = getattr(file, 'name', '文档').split('/')[-1].split('\\')[-1]
        title = filename.rsplit('.', 1)[0]
        markdown_text = [f"# {title}"]
        
        # 处理文本内容
        paragraphs = []
        current_paragraph = []
        
        # 按行分割
        for line in text.split('\n'):
            line = line.strip()
            if line:  # 非空行
                current_paragraph.append(line)
            elif current_paragraph:  # 空行且有累积的段落内容
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        # 处理最后一个段落
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # 将段落添加到markdown文本中
        markdown_text.extend(paragraphs)
        
        return "\n\n".join(markdown_text)
    
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

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
