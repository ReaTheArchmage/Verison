proc = "proc"
divisor = ':'

#region HEAD DECLARATION PARSING:

def OpenFile(path):
    with open(path, 'r') as f:
        for line in f:
            print(ParseProcedureDeclaration(
                line.rstrip("\n")))

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
    return line[div_idx+1: div_idx+end_idx], div_idx+end_idx

def FindParameters(line, index):
    params_block = line[index:]
    if params_block.startswith("(") and params_block.endswith(")"):
        return params_block[1:-1]
    return "Syntax error, arguments must be in parenthesis."

def FormatParameters(params):
    parameter_number = (params.count(",")) + 1
    next_comma = 0
    for i in range(parameter_number):
        pass

def ParseProcedureDeclaration(line):
    procedure_dec, proc_idx = FindProcedureDeclaration(line)
    ret_type = FindReturnType(line, proc_idx)
    name, params_idx = FindName(line)
    parameters = FindParameters(line, params_idx)
    FormatParameters(parameters)

    return {"return type" : ret_type,
            "name": name,
            "parameters" : parameters}

#endregion