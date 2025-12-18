import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 filter.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # 读取原始行，去重去空
            raw_lines = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return

    # 1. 建立索引 (Sets)
    # 用来快速查询是否存在某个“更强”的规则
    # 存储的内容都是去除前缀后的“根域名”
    
    roots_plus = set()  # 对应 +.domain
    roots_dot = set()   # 对应 .domain
    roots_star = set()  # 对应 *.domain

    parsed_rules = []   # 存储 (type, domain, original_line)

    for line in raw_lines:
        if line.startswith('+.'):
            domain = line[2:]
            roots_plus.add(domain)
            parsed_rules.append(('plus', domain, line))
        elif line.startswith('*.'):
            domain = line[2:]
            roots_star.add(domain)
            parsed_rules.append(('star', domain, line))
        elif line.startswith('.'):
            domain = line[1:]
            roots_dot.add(domain)
            parsed_rules.append(('dot', domain, line))
        elif line == '*':
            # 特殊规则 *，通常不进行层级处理，直接保留或仅被完全通配符覆盖
            # 这里将其视为 exact 类型的一个特例，或者单独类型
            parsed_rules.append(('wildcard_all', '*', line))
        else:
            # 精确匹配
            parsed_rules.append(('exact', line, line))

    final_lines = []

    # 2. 遍历检查每条规则是否冗余
    for r_type, domain, line in parsed_rules:
        is_redundant = False
        
        # 特殊处理全匹配 *
        if r_type == 'wildcard_all':
            final_lines.append(line)
            continue

        # --- A. 检查“同域名”的更强规则覆盖 ---
        # 例如：如果存在 +.baidu.com，那么 .baidu.com, *.baidu.com, baidu.com 都是多余的
        
        # 如果当前不是 plus，但存在同名的 plus，删
        if r_type != 'plus' and domain in roots_plus:
            is_redundant = True
        
        # 如果当前是 star (*.d)，但存在同名的 dot (.d)，删 (因为 .d 包含 *.d)
        if r_type == 'star' and domain in roots_dot:
            is_redundant = True

        # 注意：.d 不覆盖 d (exact)，*.d 也不覆盖 d (exact)，所以这里不用检查 exact
        
        if is_redundant:
            continue

        # --- B. 检查“父级域名”的规则覆盖 ---
        parts = domain.split('.')
        
        # 遍历所有父级
        # 例如 tieba.baidu.com -> 检查 baidu.com, com
        for i in range(len(parts) - 1):
            parent = '.'.join(parts[i+1:])
            
            # 1. 父级有 +. (Suffix)
            # +.baidu.com 覆盖所有子域 (tieba.baidu.com, *.tieba..., .tieba...)
            if parent in roots_plus:
                is_redundant = True
                break
            
            # 2. 父级有 . (Dot)
            # .baidu.com 覆盖所有子域
            if parent in roots_dot:
                is_redundant = True
                break
            
            # 3. 父级有 *. (Star)
            # *.baidu.com 只覆盖“直接下一级”的“精确匹配”
            # 只有当当前规则是 'exact' 且距离父级正好是 1 层时，才算被覆盖
            # 例如：*.baidu.com 覆盖 tieba.baidu.com
            # 但不覆盖 123.tieba.baidu.com (距离2)，也不覆盖 *.tieba.baidu.com
            if parent in roots_star:
                if r_type == 'exact' and i == 0: # i==0 表示直接父级
                    is_redundant = True
                    break

        if not is_redundant:
            final_lines.append(line)

    # 3. 排序并写入
    # 按照：符号优先，然后长度短优先，最后字母顺序
    # 这样 +.baidu.com 会排在 baidu.com 前面，看起来整齐
    def sort_key(l):
        # 权重：+. 最前, *. 次之, . 再次, 普通最后
        prefix_score = 4
        if l.startswith('+.'): prefix_score = 1
        elif l.startswith('*.'): prefix_score = 2
        elif l.startswith('.'): prefix_score = 3
        return (prefix_score, len(l), l)

    final_lines.sort(key=sort_key)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines) + '\n')

if __name__ == "__main__":
    main()