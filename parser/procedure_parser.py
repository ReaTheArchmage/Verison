proc = "proc"
divisor = ':'


def FindProcedureDeclaration(line):
    proc_idx = line.find(proc)
    if proc_idx != -1:
        return proc, proc_idx
    return "Syntax error, procedure unspecified", -1


def FindReturnType(line, index):
    type_ = line[:index]
    if type_.startswith("(") and type_.endswith(")"):
        return type_[1:-1]
    return "Syntax error, missing parenthesis for return."


def FindName(line):
    div_idx = line.find(divisor)
    tmp_name = line[div_idx:]
    end_idx = tmp_name.find("(")
    return line[div_idx + 1: div_idx + end_idx].strip(), div_idx + end_idx


def FindParameters(line, index):
    # index points at the "(" that opens the parameter list. Matching the
    # closing ")" directly (rather than checking how the whole line ends)
    # is what lets a trailing body colon, e.g. "...(x i32, y i32):", parse
    # correctly instead of always reporting a syntax error.
    if index >= len(line) or line[index] != "(":
        return "Syntax error, arguments must be in parenthesis."
    end = line.find(")", index)
    if end == -1:
        return "Syntax error, arguments must be in parenthesis."
    return line[index + 1:end]


def ParseProcedureDeclaration(line):
    line = line.lstrip()  # tabs or stray spaces, same reasoning as field_parser

    procedure_dec, proc_idx = FindProcedureDeclaration(line)
    ret_type = FindReturnType(line, proc_idx)
    name, params_idx = FindName(line)
    parameters = FindParameters(line, params_idx)

    return {"return_type": ret_type,
            "name": name,
            "parameters": parameters}