from PyPDF2 import PdfReader
import sys
import pdfplumber

def is_same_paragraph(current_line, next_line):
    """判断两行是否属于同一段落"""
    current = current_line.strip()
    next_line = next_line.strip()
    
    # 如果当前行为空或下一行为空，不属于同一段
    if not current or not next_line:
        return False
    
    # 如果当前行以特定标点结尾，不属于同一段
    if current.rstrip().endswith(('.', '。', '!', '?', '！', '？')):
        return False
    
    # 如果下一行以数字、特殊符号或中文标点开头，不属于同一段
    if next_line.lstrip()[0] in ('•', '·', '○', 'Ø', '》', '、') or next_line.lstrip()[0].isdigit():
        return False
    
    def is_chinese_char(char):
        return '\u4e00' <= char <= '\u9fff'
    
    # 去除尾部空格后再判断最后一个字符
    current_end_is_chinese = is_chinese_char(current.rstrip()[-1])
    # 去除头部空格后再判断第一个字符
    next_start_is_chinese = is_chinese_char(next_line.lstrip()[0])

    # 如果当前行结尾是间断标点，认为是同一段
    if current.rstrip().endswith(('，', ',', ';', '；')):
        return True
    
    # 如果当前行结尾是英文单词的一部分，且下一行开头是英文字母，认为是同一段
    if (not current_end_is_chinese and current.rstrip()[-1].isalpha() and 
        not next_start_is_chinese and next_line.lstrip()[0].isalpha()):
        return True
    
    # 如果当前行结尾和下一行开头都是中文，认为是同一段
    if current_end_is_chinese and next_start_is_chinese:
        return True
    
    return False

def is_title(current_line, next_line):
    """判断当前行是否是标题"""
    current = current_line.strip()
    next_line = next_line.strip()
    
    # 如果是空行，不是标题
    if not current:
        return False
        
    # 如果以冒号结尾，是标题
    if current.endswith((':', '：')):
        return True
        
    # 检查是否以中文数字开头加点
    chinese_numbers = '一二三四五六七八九十'
    for numeral in chinese_numbers:
        if current.startswith(f"{numeral}.") or current.startswith(f"{numeral}、"):
            return True

    # 检查是否以罗马数字开头加点
    roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
    for numeral in roman_numerals:
        if current.startswith(f"{numeral}.") or current.startswith(f"{numeral}、"):
            return True

    # 检查是否以阿拉伯数字开头加点
    if len(current) >= 2:
        first_char = current[0]
        second_char = current[1]
        if first_char.isdigit() and (second_char == '.' or second_char == '、'):
            return True

    # 如果长度小于20且不以句子结束符号结尾
    sentence_endings = ('.', '。', '!', '?', '！', '？')
    if len(current) < 20 and not any(current.endswith(end) for end in sentence_endings):
        return True
        
    return False

def extract_tables_to_markdown(pdf_path):
    markdown_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue

                # 去掉空行
                table = [row for row in table if row and any(cell and cell.strip() for cell in row)]

                if len(table) < 2:
                    continue  # 必须要有表头 + 至少一行数据

                header = table[0]
                rows = table[1:]

                # 输出 header
                markdown_tables.append("|" + "|".join(cell.strip().replace("\n", "") if cell else "" for cell in header) + "|")

                # Markdown 的分隔符
                markdown_tables.append("|" + "|".join("---" for _ in header) + "|")

                # 输出数据行
                for row in rows:
                    clean_row = [cell.strip().replace("\n", "") if cell else "" for cell in row]
                    markdown_tables.append("|" + "|".join(clean_row) + "|")

                markdown_tables.append("")  # 分隔多个表格

    return '\n'.join(markdown_tables)

def merge_text_with_tables(text, tables_markdown):
    """将原文本中的表格部分替换为markdown格式的表格
    
    Args:
        text: 原始提取的文本
        tables_markdown: 通过extract_tables_to_markdown提取的表格
    """
    if not tables_markdown:
        return text
        
    # 将文本按段落分割
    paragraphs = text.split('\n\n')
    result_paragraphs = []
    
    # 解析表格内容，创建查找表
    tables = tables_markdown.split('\n\n')
    for table in tables:
        if not table.strip():
            continue
            
        # 获取表格的行数据（去掉markdown分隔符）
        table_rows = [row.strip('|').split('|') for row in table.split('\n') 
                     if row.strip() and not row.strip('|').startswith('---')]
        if not table_rows:
            continue
            
        # 创建表格内容的指纹
        table_content = []
        for row in table_rows:
            row = [cell.strip() for cell in row]
            # 将每行的前两个单元格作为识别依据
            if len(row) >= 2:
                table_content.append((row[0].strip(), row[1].strip()))
        
        # 在原文中查找和替换表格内容
        found_start = -1
        for i, para in enumerate(paragraphs):
            # 检查段落是否包含表格的第一行
            if table_content and table_content[0][0] in para and table_content[0][1] in para:
                found_start = i
                break
        
        if found_start >= 0:
            # 确定表格在原文中的范围
            found_end = found_start
            matched_rows = 1
            for i in range(found_start + 1, len(paragraphs)):
                para = paragraphs[i]
                for name, desc in table_content[matched_rows:]:
                    if name in para and desc in para:
                        found_end = i
                        matched_rows += 1
                        break
                if matched_rows >= len(table_content):
                    break
            
            # 替换原文中的表格内容
            if found_start <= found_end:
                result_paragraphs.extend(paragraphs[:found_start])
                result_paragraphs.append(table)
                paragraphs = paragraphs[found_end + 1:]
            else:
                result_paragraphs.append(paragraphs.pop(0))
        else:
            result_paragraphs.append(paragraphs.pop(0))
    
    # 添加剩余的段落
    result_paragraphs.extend(paragraphs)
    
    return '\n\n'.join(result_paragraphs)

def extract_pdf_text(pdf_path):
    """从PDF文件中提取文本并返回markdown格式的文本"""
    try:
        # 获取表格
        tables_markdown = extract_tables_to_markdown(pdf_path)
        
        # 原有的文本提取逻辑
        reader = PdfReader(pdf_path)
        current_paragraph = []
        result_text = []
        
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            text = text.strip()
            if text and text[0].isdigit():
                for i, char in enumerate(text):
                    if not char.isdigit():
                        text = text[i:].strip()
                        break
            
            lines = text.splitlines()
            if len(lines) >= 3 and lines[-3].strip() == "_":
                lines = lines[:-3]
            
            # 处理当前页的每一行
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                current_paragraph.append(line.strip())
                
                should_output = False
                is_title_line = False
                
                if i == len(lines) - 1:
                    if page_num < len(reader.pages):
                        next_page_text = reader.pages[page_num].extract_text()
                        next_page_lines = next_page_text.splitlines()
                        if next_page_lines:
                            first_valid_line = next(
                                (l for l in next_page_lines if l.strip()), 
                                None
                            )
                            if not first_valid_line:
                                should_output = True
                            elif is_title(line, first_valid_line):
                                should_output = True
                                is_title_line = True
                            elif not is_same_paragraph(line, first_valid_line):
                                should_output = True
                    else:
                        should_output = True
                else:
                    next_line = lines[i + 1]
                    if is_title(line, next_line):
                        should_output = True
                        is_title_line = True
                    elif not is_same_paragraph(line, next_line):
                        should_output = True
                
                # 添加段落到结果中
                if is_title_line and current_paragraph and should_output:
                    result_text.append("# " + "".join(current_paragraph))
                    current_paragraph = []
                elif should_output and current_paragraph:
                    result_text.append("".join(current_paragraph))
                    current_paragraph = []
        
        # 确保最后一个段落被添加
        if current_paragraph:
            result_text.append(" ".join(current_paragraph))
        
        # 合并文本和表格
        text = "\n\n".join(result_text)
        if not tables_markdown:
            return text
        return merge_text_with_tables(text, tables_markdown)
            
    except Exception as e:
        print(f"提取PDF文本时出错: {str(e)}", file=sys.stderr)
        return ""

if __name__ == "__main__":
    input_file = "rag/test_docs/AI信息化在华通公司的实施方案v1.1.pdf"
    #print("提取PDF文本...")
    text = extract_pdf_text(input_file)
    print(text)
    #tables = extract_tables_to_markdown(input_file)
    #print(tables)
