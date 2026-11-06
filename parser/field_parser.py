var,const = "var", "const"
rust_var, rust_const = "let mut", const
file_path = "tests/field_syntax_test.verison"
ERR = "SYNTAX ERROR"

def OpenFile(path):
    with open(path, 'r') as f:
        for line in f:
            print(ParseField(line))

def ParseField(line):
    f_idx, field = FindFieldDef(line)
    type_ = FindType(line, f_idx)
    listed_line = {type_,field}
    return listed_line

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
        print(f"Warning: no ':' found in: {line!r}")
        return ""

    value = line[declar_idx + 1:].strip()
    if not value:
        print(f"Warning: no value found after ':' in: {line!r}")
        return ""

    return declar_idx, value

def FindName(line, index):
    if index + 1 >= len(line) or line[index + 1] != " ":
        print(f"Warning: expected space after declarator in: {line!r}")
    i = index - 1
    while i >= 0 and line[i] == " ":
        i -= 1
    end = i + 1
    while i >= 0 and line[i] != " ":
        i -= 1
    start = i + 1
    return line[start:end]

curr_file = OpenFile()
