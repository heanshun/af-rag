import re
import os
import pdfplumber
import docx
import openpyxl
from bs4 import BeautifulSoup

def convert_to_markdown(filepath: str, filetype: str) -> str:
    if filetype == 'pdf':
        text = extract_pdf(filepath)
    elif filetype == 'docx':
        text = extract_docx(filepath)
    elif filetype == 'xlsx':
        text = extract_excel(filepath)
    elif filetype == 'html' or filetype == 'htm':
        text = extract_html(filepath)
    elif filetype == 'txt':
        text = extract_txt(filepath)
    else:
        raise ValueError(f"Unsupported file type: {filetype}")
    
    return format_to_markdown(text)

def extract_pdf(filepath):
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_docx(filepath):
    doc = docx.Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_excel(filepath):
    wb = openpyxl.load_workbook(filepath, data_only=True)
    text = ""
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            line = " ".join([str(cell) if cell is not None else '' for cell in row])
            text += line + "\n"
    return text

def extract_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    return soup.get_text(separator='\n')

def extract_txt(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def format_to_markdown(text):
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    output = []
    for idx, para in enumerate(paragraphs, 1):
        # 将中文句子按 。！？ 分行，但保持为同一段
        para = re.sub(r'([。！？\?！])([^”’])', r'\1\n\2', para)
        output.append(f"# 第{idx}章\n{para}")
    return "\n\n".join(output)


if __name__ == "__main__":
    markdown_text = convert_to_markdown("rag/test_docs/txtTest.txt")
    print(markdown_text)
    markdown_text = convert_to_markdown("rag/test_docs/docxTest.docx")
    print(markdown_text)
