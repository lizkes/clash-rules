import argparse
import os
import sys
import re

# --- 来自 raw2yaml.py 的常量与逻辑 ---

TYPE_EXACT = 'exact'   # google.com
TYPE_PLUS = 'plus'     # +.google.com (全匹配：本身+多级子域)
TYPE_STAR = 'star'     # *.google.com (仅单级子域)
TYPE_DOT = 'dot'       # .google.com  (仅多级子域，不含本身)

def parse_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # 清理可能残留的 YAML 格式或其他符号
    if line.startswith("-"):
        line = re.sub(r"^-\s*['\"]?|['\"]?$", "", line)

    domain = ""
    rule_type = TYPE_EXACT

    # 1. 识别前缀 (v2ray/clash/raw 常见格式)
    if line.startswith("full:"):
        domain = line[5:]
        rule_type = TYPE_EXACT
    elif line.startswith("domain:"):
        domain = line[7:]
        rule_type = TYPE_PLUS
    
    # 2. 识别符号前缀
    elif line.startswith("+."):
        domain = line[2:]
        rule_type = TYPE_PLUS
    elif line.startswith("*."):
        domain = line[2:]
        rule_type = TYPE_STAR
    elif line.startswith("."):
        domain = line[1:]
        rule_type = TYPE_DOT
    
    # 3. 识别特殊符号
    elif line.startswith("*"):
        if line.startswith("*."):
            domain = line[2:]
            rule_type = TYPE_STAR
        else:
            domain = line.lstrip("*")
            rule_type = TYPE_STAR
    else:
        domain = line
        rule_type = TYPE_EXACT

    return domain.strip(), rule_type

def optimize_rules(rules_list):
    """
    去除冗余规则：
    如果存在 +.google.com，则删除 a.google.com, b.a.google.com 等
    """
    plus_roots = set()
    for domain, r_type in rules_list:
        if r_type == TYPE_PLUS:
            plus_roots.add(domain)

    final_rules = []
    removed_count = 0

    for domain, r_type in rules_list:
        is_redundant = False
        parts = domain.split('.')
        
        # Check 1: 父级覆盖 (检查是否被已有的根域名涵盖)
        for i in range(len(parts) - 1):
            parent = ".".join(parts[i+1:])
            if parent in plus_roots:
                is_redundant = True
                break
        
        # Check 2: 同级覆盖 (如果自身是 +.domain，且规则也是 +.domain，则不视为冗余；
        # 但如果自身是精确匹配 domain，而存在 +.domain，则精确匹配是冗余的)
        if not is_redundant:
            if domain in plus_roots:
                # 如果当前规则不是 PLUS 类型，但存在对应的 PLUS 根域名，则当前规则冗余
                if r_type in [TYPE_EXACT, TYPE_STAR, TYPE_DOT]:
                    is_redundant = True

        if is_redundant:
            removed_count += 1
        else:
            final_rules.append((domain, r_type))

    # 去重 (使用 dict key 特性)
    unique_map = {}
    for d, t in final_rules:
        unique_map[(d, t)] = True
    
    if removed_count > 0:
        print(f"  - Optimization: Removed {removed_count} redundant rules.")
        
    return list(unique_map.keys())

def get_sort_key(item):
    # 按域名层级倒序排序 (com.google, com.apple)
    return item[0].split('.')[::-1]

# --- 原 merge_raw.py 的文件读取逻辑 ---

def read_lines_to_set(filepaths):
    """
    读取排除文件列表，返回一个集合用于快速查找。
    这里存储原始行内容，用于精确剔除。
    """
    lines_set = set()
    if not filepaths:
        return lines_set

    for path in filepaths:
        if not os.path.exists(path):
            print(f"Warning: Drop file not found: {path}")
            continue
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    content = line.strip()
                    if content and not content.startswith("#"):
                        lines_set.add(content)
                        # 为了增强排除能力，也可以尝试解析后加入 set
                        # 但为保持简单，这里暂只匹配原始文本
        except Exception as e:
            print(f"Error reading {path}: {e}")
            
    return lines_set

def merge_files(inputs, output, drops):
    # 1. 准备排除名单
    drop_set = read_lines_to_set(drops)
    if drop_set:
        print(f"Loaded {len(drop_set)} specific lines to exclude.")

    raw_parsed_rules = []
    
    # 2. 读取并收集所有规则
    for input_path in inputs:
        if not os.path.exists(input_path):
            print(f"Warning: Input file not found: {input_path}")
            continue
        
        print(f"Reading: {input_path} ...")
        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                for line in infile:
                    content = line.strip()
                    if not content:
                        continue
                    
                    # 检查是否在排除列表中 (原始文本匹配)
                    if content in drop_set:
                        continue

                    # 解析行
                    parsed = parse_line(content)
                    if parsed:
                        raw_parsed_rules.append(parsed)
                        
        except Exception as e:
            print(f"Error reading {input_path}: {e}")

    # 3. 执行优化 (去重、去冗余)
    print(f"Processing {len(raw_parsed_rules)} rules...")
    optimized_list = optimize_rules(raw_parsed_rules)
    
    # 4. 排序
    optimized_list.sort(key=get_sort_key)

    # 5. 写入文件 (还原为 Raw 格式)
    try:
        with open(output, 'w', encoding='utf-8') as outfile:
            for domain, r_type in optimized_list:
                line_to_write = ""
                
                # 根据类型还原前缀，生成标准化的 Raw 文件
                if r_type == TYPE_PLUS:
                    line_to_write = f"+.{domain}"
                elif r_type == TYPE_STAR:
                    line_to_write = f"*.{domain}"
                elif r_type == TYPE_DOT:
                    line_to_write = f".{domain}"
                else: # TYPE_EXACT
                    line_to_write = domain
                
                outfile.write(line_to_write + '\n')
                
        print(f"Success: Merged and optimized rules written to '{output}'. (Total: {len(optimized_list)})")

    except Exception as e:
        print(f"Fatal error writing to {output}: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Merge raw domain lists with optimization and sorting.")
    
    # -i: 输入文件列表
    parser.add_argument('-i', '--input', nargs='+', required=True, 
                        help="List of input raw file paths")
    
    # -d: 排除文件列表
    parser.add_argument('-d', '--drop', nargs='*', default=[], 
                        help="List of raw file paths to exclude")
    
    # -o: 输出文件路径
    parser.add_argument('-o', '--output', required=True, 
                        help="Output raw file path")

    args = parser.parse_args()

    merge_files(args.input, args.output, args.drop)

if __name__ == "__main__":
    main()