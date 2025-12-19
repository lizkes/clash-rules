import sys
import re
import os
import argparse

# 定义通配符类型常量
TYPE_EXACT = 'exact'   # google.com
TYPE_PLUS = 'plus'     # +.google.com (全匹配：本身+多级子域)
TYPE_STAR = 'star'     # *.google.com (仅单级子域)
TYPE_DOT = 'dot'       # .google.com  (仅多级子域，不含本身)

def parse_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # 清理 YAML 可能残留的格式
    if line.startswith("-"):
        line = re.sub(r"^-\s*['\"]?|['\"]?$", "", line)

    domain = ""
    rule_type = TYPE_EXACT

    # 1. 识别前缀 (v2ray/clash 格式)
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
    plus_roots = set()
    for domain, r_type in rules_list:
        if r_type == TYPE_PLUS:
            plus_roots.add(domain)

    final_rules = []
    removed_count = 0

    for domain, r_type in rules_list:
        is_redundant = False
        parts = domain.split('.')
        
        # Check 1: 父级覆盖
        for i in range(len(parts) - 1):
            parent = ".".join(parts[i+1:])
            if parent in plus_roots:
                is_redundant = True
                break
        
        # Check 2: 同级覆盖
        if not is_redundant:
            if domain in plus_roots:
                if r_type in [TYPE_EXACT, TYPE_STAR, TYPE_DOT]:
                    is_redundant = True

        if is_redundant:
            removed_count += 1
        else:
            final_rules.append((domain, r_type))

    unique_map = {}
    for d, t in final_rules:
        unique_map[(d, t)] = True
    
    if removed_count > 0:
        print(f"  - Optimization: Removed {removed_count} redundant rules.")
        
    return list(unique_map.keys())

def get_sort_key(item):
    return item[0].split('.')[::-1]

def convert_file(input_path, output_path, keep_input):
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        sys.exit(1)

    # 逻辑：如果没有指定 -o，则生成同名 .yaml 文件
    if not output_path:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}.yaml"

    try:
        with open(input_path, 'r', encoding='utf-8') as fin:
            lines = fin.readlines()
        
        raw_parsed = []
        for line in lines:
            res = parse_line(line)
            if res:
                raw_parsed.append(res)
        
        optimized_list = optimize_rules(raw_parsed)
        optimized_list.sort(key=get_sort_key)

        with open(output_path, 'w', encoding='utf-8') as fout:
            fout.write("payload:\n")
            for domain, r_type in optimized_list:
                if r_type == TYPE_PLUS:
                    fout.write(f"  - '+.{domain}'\n")
                elif r_type == TYPE_STAR:
                    fout.write(f"  - '*.{domain}'\n")
                elif r_type == TYPE_DOT:
                    fout.write(f"  - '.{domain}'\n")
                else:
                    fout.write(f"  - {domain}\n")
        
        print(f"Success: '{input_path}' -> '{output_path}' (Total: {len(optimized_list)})")

        # 默认删除输入文件
        if not keep_input:
            # 确保不会删掉刚生成的输出文件（防误伤）
            if os.path.abspath(input_path) != os.path.abspath(output_path):
                os.remove(input_path)
                print(f"Removed input file: {input_path}")

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert raw domain list to Clash YAML rule-set.")
    parser.add_argument("-i", "--input", required=True, help="Path to input text file")
    parser.add_argument("-o", "--output", help="Path to output YAML file (optional)")
    parser.add_argument("--keep", action="store_true", help="Keep input file after conversion")

    args = parser.parse_args()
    
    convert_file(args.input, args.output, args.keep)