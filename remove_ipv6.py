import argparse
import sys
import ipaddress
import os

def is_ipv6(cidr_str):
    """
    判断字符串是否为 IPv6 地址或网段
    """
    cidr_str = cidr_str.strip()
    if ':' not in cidr_str:
        return False
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        return network.version == 6
    except ValueError:
        return False

def process_raw_list(input_path, output_path, keep_source):
    try:
        if not os.path.exists(input_path):
            print(f"Error: Input file '{input_path}' not found.")
            sys.exit(1)

        # 1. 读取内容
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        kept_lines = []
        ipv6_count = 0
        misc_removed_count = 0 # 统计删除的空行和注释
        
        # 2. 遍历处理
        for line in lines:
            content = line.strip()
            
            # --- 规则 A: 删除空行 ---
            if not content:
                misc_removed_count += 1
                continue

            # --- 规则 B: 删除注释行 ---
            if content.startswith("#"):
                misc_removed_count += 1
                continue

            # --- 规则 C: 删除 IPv6 ---
            if is_ipv6(content):
                ipv6_count += 1
                continue 
            
            # --- 规则 D: 保留 IPv4 ---
            # 重新加上换行符，确保输出文件整洁，无多余空格
            kept_lines.append(content + '\n')
            
        # 3. 写入新文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(kept_lines)
            
        print(f"Success: Processed {input_path}")
        print(f"  - Removed {ipv6_count} IPv6 addresses.")
        print(f"  - Removed {misc_removed_count} comments/empty lines.")
        print(f"  -> Saved to: {output_path}")

        # 4. 处理源文件删除逻辑
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
            print(f"  -> Source file kept: {input_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Clean Raw List: Remove IPv6, comments, and empty lines.")
    
    parser.add_argument('-i', '--input', required=True, 
                        help="Input file path")
    
    parser.add_argument('-o', '--output', required=False, 
                        help="Output file path. Defaults to input filename with .list extension.")
    
    parser.add_argument('--keep', action='store_true', 
                        help="Keep the source file. If not specified, source file will be deleted.")
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output

    if not output_path:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.list"
    
    process_raw_list(input_path, output_path, args.keep)

if __name__ == "__main__":
    main()