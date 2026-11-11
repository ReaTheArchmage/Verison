var, const, field = "var", "const", "field"
ERR = "SYNTAX ERROR"


def FindFieldDef(line):
    var_idx = line.find(var)
    const_idx = line.find(const)
    field_idx = line.find(field)

    if var_idx != -1:
        return var_idx, var
    if const_idx != -1:
        return const_idx, const
    if field_idx != -1:
        return field_idx, field

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
        return -1, ""

    value = line[declar_idx + 1:].strip()
    if not value:
        print(f"Warning: no value found after ':' in: {line!r}")
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


def ParseFieldDeclaration(line):
    # strip all leading whitespace first (tabs for real indentation, but
    # also any stray spaces) - a field inside a proc block still starts
    # with "(type)" at position 0 once that's gone, otherwise FindType's
    # startswith("(") check fails on every indented line.
    line = line.lstrip()

    f_idx, field = FindFieldDef(line)
    type_ = FindType(line, f_idx)
    name = FindName(line, f_idx)
    _, value = FindValue(line)

    return {"type": type_, "field": field,
            "name": name, "value": value}
