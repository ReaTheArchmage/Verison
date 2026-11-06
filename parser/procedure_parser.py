import verison

""" PARSE DECLARED PROCEDURES:
    this section is used to parse declared procedures 
    from verison to rust, line by line. For now, it
    doesn't support multi-line declarations.
""" 
#type, definition_divisor, name, parameters, end_of_definition

file_path = "tests/procedure_syntax_test.verison"
proc = "proc"
divisor = ':'

def OpenFile(path):
    with open(path, 'r') as f:
        for line in f:
            PrintPrettyLine(line.rstrip("\n"))

def FindProcedure(line):
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
    #print(div_idx, tmp_name, end_idx)
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

def PrintPrettyLine(line):
    procedure_dec, proc_idx = FindProcedure(line)
    ret_type = FindReturnType(line, proc_idx)
    name, params_idx = FindName(line)
    parameters = FindParameters(line, params_idx)
    FormatParameters(parameters)
    """
    print(
        "return type: ", ret_type, "\n",
        "name: ", name, "\n",
        "parameters: ", parameters, "\n",
    )
    """
curr_line = OpenFile(file_path)