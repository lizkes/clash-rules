import argparse
import sys
import ipaddress
import os

def is_ipv6(cidr_str):
    """
    判断字符串是否为 IPv6 地址或网段
    """
    cidr_str = cidr_str.strip().strip("'").strip('"')
    if ':' not in cidr_str:
        return False
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        return network.version == 6
    except ValueError:
        return False

def process_yaml(input_path, output_path, keep_source):
    try:
        # 1. 读取内容
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        kept_lines = []
        removed_count = 0
        
        # 2. 过滤 IPv6
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('-'):
                content = stripped.lstrip('-').strip()
                if is_ipv6(content):
                    removed_count += 1
                    continue
            kept_lines.append(line)
            
        # 3. 写入新文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(kept_lines)
            
        print(f"Success: Processed. Removed {removed_count} IPv6 rules.")
        print(f"  -> Saved to: {output_path}")

        # 4. 根据参数决定是否删除源文件
        # 注意：如果输入路径和输出路径相同（原地修改），则不执行删除，否则文件就没了
        abs_input = os.path.abspath(input_path)
        abs_output = os.path.abspath(output_path)

        if not keep_source:
            if abs_input != abs_output:
                try:
                    os.remove(input_path)
                    print(f"  -> Source file deleted: {input_path}")
                except OSError as e:
                    print(f"  -> Warning: Failed to delete source file: {e}")
            else:
                # 原地修改模式，不需要删除源文件（因为它已经被覆盖了）
                pass
        else:
            print(f"  -> Source file kept: {input_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Remove IPv6 addresses from YAML.")
    
    # -i 仍然是必须的
    parser.add_argument('-i', '--input', required=True, 
                        help="Input file path")
    
    # -o 变为可选
    parser.add_argument('-o', '--output', required=False, 
                        help="Output YAML file path. Defaults to input filename with .yaml extension.")
    
    # --keep 开关 (store_true 表示出现该参数为 True，否则为 False)
    parser.add_argument('--keep', action='store_true', 
                        help="Keep the source file. If not specified, source file will be deleted.")
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output

    # 如果没有指定输出路径，自动生成
    if not output_path:
        # 获取文件名（不含扩展名）
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.yaml"
    
    process_yaml(input_path, output_path, args.keep)

if __name__ == "__main__":
    main()