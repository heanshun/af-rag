from pathlib import Path
from bs4 import BeautifulSoup
import docx
import pandas as pd
from PyPDF2 import PdfReader
import re
from pdf2docx import Converter

def convert_docx_to_markdown(filepath):
    doc = docx.Document(filepath)
    markdown_lines = []
    has_heading = False
    para_index = 0

    for element in doc.element.body:
        if element.tag.endswith('tbl'):  # 表格处理
            table = []
            for row in element.findall('.//w:tr', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                cells = []
                for cell in row.findall('.//w:t', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                    cells.append(cell.text)
                if cells:
                    table.append('|' + '|'.join(cells) + '|')
            
            if table:
                header_separator = '|' + '|'.join(['---'] * len(table[0].split('|')[1:-1])) + '|'
                table.insert(1, header_separator)
                markdown_lines.extend(table)
                markdown_lines.append('')  # 添加空行
        
        elif element.tag.endswith('p'):  # 段落处理
            if para_index >= len(doc.paragraphs):
                continue
                
            para = doc.paragraphs[para_index]
            text = para.text.strip()
            para_index += 1  # 增加段落索引
            
            if not text:
                continue

            style = para.style.name.lower()

            punctuation = '。！？，；,.!?;'  # 定义标点符号
            if "heading" in style:
                level = 1  # 所有标题都处理为一级标题
                markdown_lines.append(f"# {text}")
                has_heading = True
            elif len(text) <= 20 and text[-1] not in punctuation:  # 新增判断条件
                markdown_lines.append(f"# {text}")
                has_heading = True
            elif "list" in style or para._element.xpath(".//w:numPr"):
                markdown_lines.append(f"- {text}")
            else:
                markdown_lines.append(text)

    if not has_heading and markdown_lines:
        markdown_lines.insert(0, "# 第一段")

    return '\n\n'.join(markdown_lines)

def convert_pdf_to_markdown(pdf_path):
    pdf_path = Path(pdf_path)
    docx_path = pdf_path.with_suffix('.converted.docx')
    
    # Step 1: Convert PDF to DOCX
    converter = Converter(str(pdf_path))
    converter.convert(str(docx_path))
    converter.close()
    
    # Step 2: Convert DOCX to Markdown
    markdown_text = convert_docx_to_markdown(docx_path)
    
    # Step 3: 删除临时生成的 docx 文件
    docx_path.unlink()  # 使用 Path 对象的 unlink() 方法删除文件
    
    return markdown_text

def convert_txt_to_markdown(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if paragraphs:
        paragraphs.insert(0, "# 第一段")
    return '\n\n'.join(paragraphs)

def convert_html_to_markdown(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    markdown_lines = []
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
        if tag.name.startswith('h'):
            level = int(tag.name[1])
            markdown_lines.append(f"{'#' * level} {tag.get_text(strip=True)}")
        elif tag.name == 'li':
            markdown_lines.append(f"- {tag.get_text(strip=True)}")
        else:
            markdown_lines.append(tag.get_text(strip=True))

    if not any(line.startswith('#') for line in markdown_lines) and markdown_lines:
        markdown_lines.insert(0, "# 第一段")

    return '\n\n'.join(markdown_lines)

def convert_xlsx_to_markdown(filepath):
    dfs = pd.read_excel(filepath, sheet_name=None)
    markdown_lines = []

    for sheet_name, df in dfs.items():
        markdown_lines.append(f"# {sheet_name}")
        
        # 处理每个表格
        if not df.empty:
            # 获取表头
            headers = df.columns.tolist()
            # 创建表格行
            table = ['|' + '|'.join(str(col) for col in headers) + '|']
            # 添加分隔行
            table.append('|' + '|'.join(['---'] * len(headers)) + '|')
            # 添加数据行
            for _, row in df.iterrows():
                table.append('|' + '|'.join(str(cell) for cell in row) + '|')
            # 将表格添加到markdown_lines
            markdown_lines.extend(table)
            markdown_lines.append('')  # 添加空行

    return '\n\n'.join(markdown_lines)

def convert_to_markdown(filepath, filetype):
    # 获取不带扩展名的文件名
    filename = Path(filepath).stem
    
    # 根据文件类型进行转换
    if filetype == 'docx':
        content = convert_docx_to_markdown(filepath)
    elif filetype == 'pdf':
        content = convert_pdf_to_markdown(filepath)
    elif filetype == 'txt':
        content = convert_txt_to_markdown(filepath)
    elif filetype == 'html':
        content = convert_html_to_markdown(filepath)
    elif filetype == 'xlsx':
        content = convert_xlsx_to_markdown(filepath)
    else:
        raise ValueError(f"Unsupported file type: {filetype}")
    
    return [filename, content]

# 示例调用
if __name__ == "__main__":
    markdown_text = convert_to_markdown("rag/test_docs/奥枫软件人员信息.xlsx", "xlsx")
    print(markdown_text)