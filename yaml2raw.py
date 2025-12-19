import yaml
import sys
import os
import argparse

def convert_yaml_to_raw(input_path, output_path, keep_input):
    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        print(f"Error: Cannot find input file {input_path}")
        return False

    # 逻辑：如果没有指定 -o，则生成同名 .txt 文件
    if not output_path:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}.txt"

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        # 提取 payload 部分
        if data and 'payload' in data and isinstance(data['payload'], list):
            payload = data['payload']
        else:
            print(f"Error: No valid 'payload' list in {input_path}")
            return False

        # 写入 raw 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in payload:
                f.write(str(item).strip() + '\n')
        
        print(f"Success: {input_path} -> {output_path}")

        # 默认删除输入文件
        if not keep_input:
            os.remove(input_path)
            print(f"Removed input file: {input_path}")
        
        return True

    except Exception as e:
        print(f"Runtime Error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Clash YAML rule-set to raw text format.")
    parser.add_argument("-i", "--input", required=True, help="Path to input YAML file")
    parser.add_argument("-o", "--output", help="Path to output RAW file (optional, defaults to .txt)")
    parser.add_argument("--keep", action="store_true", help="Keep the input file after processing")

    args = parser.parse_args()
    
    success = convert_yaml_to_raw(args.input, args.output, args.keep)
    if not success:
        sys.exit(1)