import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 filter.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # 读取所有行，去重并去除空行
            lines = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return

    # 1. 提取所有“通配符根域名”
    # 只有当规则是以 "+." 开头时，它才具备消除子域名的能力
    # 例如：存在 "+.miwifi.com"，那么 "www.miwifi.com" 才是多余的
    wildcard_roots = set()
    for line in lines:
        if line.startswith('+.'):
            wildcard_roots.add(line[2:]) # 存入 "miwifi.com"

    final_lines = []
    
    # 按长度排序仅为了输出美观，逻辑上不再依赖顺序
    sorted_lines = sorted(list(lines), key=lambda x: len(x))

    for line in sorted_lines:
        # 获取纯净域名用于检查
        is_wildcard = line.startswith('+.')
        domain = line[2:] if is_wildcard else line
        
        parts = domain.split('.')
        is_redundant = False
        
        # 检查场景 A：是否存在更短的“通配符父级”？
        # 比如当前是 "www.miwifi.com"，检查是否已存在 "+.miwifi.com" 或 "+.com"
        for i in range(len(parts) - 1):
            parent = '.'.join(parts[i+1:])
            if parent in wildcard_roots:
                is_redundant = True
                break
        
        # 检查场景 B：如果当前是精确匹配，但存在同名的通配符？
        # 比如当前是 "miwifi.com" (精确)，但存在 "+.miwifi.com" (通配)
        # 此时精确匹配是多余的，因为通配符已经包含了它
        if not is_redundant and not is_wildcard:
            if domain in wildcard_roots:
                is_redundant = True

        # 只有当它不是冗余的时候才保留
        if not is_redundant:
            final_lines.append(line)
    
    # 将结果写回原文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines) + '\n')

if __name__ == "__main__":
    main()