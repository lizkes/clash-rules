import argparse
import os
import sys

def read_lines_to_set(filepaths):
    """
    读取排除文件列表，返回一个集合用于快速查找。
    会对每行进行 strip() 处理以忽略换行符差异。
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
                    # 去除首尾空白符（包括 \r, \n）
                    content = line.strip()
                    if content:
                        lines_set.add(content)
        except Exception as e:
            print(f"Error reading {path}: {e}")
            
    return lines_set

def merge_files(inputs, output, drops):
    # 1. 准备排除名单
    drop_set = read_lines_to_set(drops)
    if drop_set:
        print(f"Loaded {len(drop_set)} lines to exclude.")

    written_count = 0
    
    try:
        with open(output, 'w', encoding='utf-8') as outfile:
            # 2. 依次读取输入文件
            for input_path in inputs:
                if not os.path.exists(input_path):
                    print(f"Warning: Input file not found: {input_path}")
                    continue
                
                print(f"Merging: {input_path} ...")
                try:
                    with open(input_path, 'r', encoding='utf-8') as infile:
                        for line in infile:
                            # 3. 处理换行符差异：
                            # strip() 会去掉 \r\n, \n, \r 以及空格
                            content = line.strip()
                            
                            # 忽略空行
                            if not content:
                                continue
                            
                            # 4. 排除逻辑 (精确匹配)
                            if content in drop_set:
                                continue
                                
                            # 5. 写入文件 (强制使用 \n 换行)
                            outfile.write(content + '\n')
                            written_count += 1
                            
                except Exception as e:
                    print(f"Error processing {input_path}: {e}")
                    
        print(f"Successfully merged to '{output}'. Total lines: {written_count}")

    except Exception as e:
        print(f"Fatal error writing to {output}: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Merge raw files with optional exclusion.")
    
    # -i: 输入文件列表 (支持多个)
    parser.add_argument('-i', '--input', nargs='+', required=True, 
                        help="List of input raw file paths")
    
    # -d: 排除文件列表 (可选，支持多个)
    parser.add_argument('-d', '--drop', nargs='*', default=[], 
                        help="List of raw file paths to exclude")
    
    # -o: 输出文件路径
    parser.add_argument('-o', '--output', required=True, 
                        help="Output raw file path")

    args = parser.parse_args()

    merge_files(args.input, args.output, args.drop)

if __name__ == "__main__":
    main()