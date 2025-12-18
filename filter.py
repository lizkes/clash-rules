import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 filter.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    
    # 读取文件，去除空白行和重复行
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = list(set(line.strip() for line in f if line.strip()))
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return

    # 辅助函数：获取纯净域名用于比较 (去除 +. 前缀)
    def get_clean(d):
        return d.replace('+.','').lstrip('.')

    # 按域名长度排序（短的在前），保证父域名（如 baidu.com）在子域名之前处理
    lines.sort(key=lambda x: len(get_clean(x)))
    
    seen_clean = set()
    final_lines = []
    
    for line in lines:
        clean = get_clean(line)
        parts = clean.split('.')
        is_redundant = False
        
        # 检查当前域名的任何父级是否存在于已保存集合中
        # 例如：处理 tieba.baidu.com 时，检查 baidu.com 是否已存在
        for i in range(len(parts) - 1):
            parent = '.'.join(parts[i+1:])
            if parent in seen_clean:
                is_redundant = True
                break
        
        # 如果该域名不是冗余的（且自身未被添加过），则保留
        if not is_redundant and clean not in seen_clean:
            seen_clean.add(clean)
            final_lines.append(line)
    
    # 将结果写回原文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines) + '\n')

if __name__ == "__main__":
    main()