var,const = "var", "const"
rust_var, rust_const = "let mut", const
ERR = "SYNTAX ERROR"

def OpenFile(path):
    with open(path, 'r') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            print(ParseField(line))

def ParseField(line):
    f_idx, field = FindFieldDef(line)
    type_ = FindType(line, f_idx)
    name = FindName(line, f_idx)
    non_, value = FindValue(line)
    return { "type": type_, "field": field,
             "name": name,  "value": value }

def FindFieldDef(line):
    var_idx = line.find(var)
    const_idx = line.find(const)

    if var_idx != -1:
        return var_idx, var
    elif const_idx != -1:
        return const_idx, const

    return -1, ERR

def FindType(line, index):
    type_ = line[:index]
    if type_.startswith("(") and type_.endswith(")"):
        return type_[1:-1]
    return ERR

def FindValue(line):
    declar_idx = line.find(":")
    if declar_idx == -1:
        print(
            f"Warning: no ':' found in: {line!r}")
        return -1, ""

    value = line[declar_idx + 1:].strip()
    if not value:
        print(
            f"Warning: no value found after ':' in: {line!r}")
        return declar_idx, ""

    return declar_idx, value

def FindName(line, index):
    keyword = var if line.startswith(var, index) else const
    start = index + len(keyword)

    while start < len(line) and line[start].isspace():
        start += 1

    end = start

    while end < len(line) and line[end] not in (" ", ":", "\t"):
        end += 1

    return line[start:end]

