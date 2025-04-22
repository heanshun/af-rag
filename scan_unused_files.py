import os
import ast
from pathlib import Path

def get_all_python_files(root_dir):
    """获取所有Python文件的路径"""
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_imports(file_path):
    """提取文件中的所有导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ''
                for name in node.names:
                    if module:
                        imports.add(f"{module}.{name.name}")
                    else:
                        imports.add(name.name)
        return imports
    except Exception as e:
        print(f"解析文件 {file_path} 时出错: {e}")
        return set()

def find_unused_files(root_dir):
    """找出未被引用的文件"""
    all_files = get_all_python_files(root_dir)
    
    # 创建文件路径到模块名的映射
    file_to_module = {}
    for file_path in all_files:
        relative_path = os.path.relpath(file_path, root_dir)
        module_name = os.path.splitext(relative_path)[0].replace(os.sep, '.')
        file_to_module[file_path] = module_name
    
    # 收集所有导入
    all_imports = set()
    for file_path in all_files:
        imports = extract_imports(file_path)
        all_imports.update(imports)
    
    # 找出未被引用的文件
    unused_files = []
    for file_path, module_name in file_to_module.items():
        if module_name not in all_imports and not file_path.endswith('run_services.py'):
            unused_files.append(file_path)
    
    return unused_files

if __name__ == '__main__':
    project_root = '.'  # 当前目录
    unused_files = find_unused_files(project_root)
    
    if unused_files:
        print("\n未被引用的文件:")
        for file in unused_files:
            print(f"- {file}")
    else:
        print("没有发现未被引用的文件")