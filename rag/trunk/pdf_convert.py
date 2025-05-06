from PyPDF2 import PdfReader
import sys

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

def extract_pdf_text(pdf_path):
    """从PDF文件中提取文本并返回markdown格式的文本"""
    try:
        reader = PdfReader(pdf_path)
        current_paragraph = []
        result_text = []  # 用于存储所有处理后的文本
        
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
        
        # 返回所有文本，用双换行符连接
        return "\n\n".join(result_text)
            
    except Exception as e:
        print(f"提取PDF文本时出错: {str(e)}", file=sys.stderr)
        return ""

if __name__ == "__main__":
    input_file = "rag/test_docs/AI信息化在华通公司的实施方案v1.1.pdf"
    print("提取PDF文本...")
    text = extract_pdf_text(input_file)
    print(text)
    