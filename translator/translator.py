class ListedField:
    def __init__(
        self, indent_lvl,field, name, type_, value): 
        
        self.indent_lvl = indent_lvl
        self.field = field
        self.name = name
        self.type_ = type_
        self.value = value

tmp_verison_field = ListedField(
    indent_lvl= 2,
    field= "var", name= "title",
    type_= "&str", value= '"Verison"'
)


def TranslateFieldDef(input_field: ListedField) -> str:

    tmp_rust_field = ListedField(
    indent_lvl= 0,
    field= "", name= "",
    type_= "", value= ""
    )

    formatted_field = ""

    EquateFieldLists(input_field, tmp_rust_field)
    formatted_field = IndentLine(input_field, formatted_field)
    
    formatted_field += (
        tmp_rust_field.field + " " +
        tmp_rust_field.name + ": " +
        tmp_rust_field.type_ + " = " +
        tmp_rust_field.value + ";"
    )

    print(formatted_field)
    return formatted_field


def IndentLine(line, modified_string : str) -> str:
    for x in range(0,line.indent_lvl):
        modified_string += "\t"
    return modified_string


def EquateFieldLists(veri_field, rust_field):

    if veri_field.field == "var":
        rust_field.field = "let"
    
    elif veri_field.field == "const":
        rust_field.field = "const"

    rust_field.indent_lvl = veri_field.indent_lvl
    rust_field.name =  veri_field.name
    rust_field.value = veri_field.value
    rust_field.type_ = veri_field.type_


class ListedProcedure:
    def __init__(
        self, field, name, returnType, parameters):

        self.field = field
        self.name = name
        self.returnType = returnType
        self.parameters = parameters

tmp_verison_procedure = ListedProcedure(
    field= "proc",
    name= "squareRoot",
    returnType="()",
    parameters={"x" : "f32", "steps" : "i32"}
)


def TranslateProcDef(input_procedure: ListedProcedure) -> str:

    tmp_rust_function = ListedProcedure(
    field= "fn", name="",
    returnType="", parameters={},
    )

    EquateProcLists(input_procedure, tmp_rust_function)

    formatted_parameters : str = ""

    for param in tmp_rust_function.parameters:
        formatted_parameters += (
            param + " : " + tmp_rust_function.parameters[param] + ", "
        )

    if formatted_parameters.endswith(","):
        formatted_parameters = formatted_parameters[0:-1]   

    formatted_procedure: str = (
        tmp_rust_function.field + " " +
        tmp_rust_function.name + "(" +
        formatted_parameters + ") -> " +
        tmp_rust_function.returnType + " {"
    )

    print(formatted_procedure)
    return formatted_procedure


def EquateProcLists(veri_proc, rust_proc):
    rust_proc.name= veri_proc.name
    rust_proc.returnType= veri_proc.returnType
    rust_proc.parameters= veri_proc.parameters


class LogicalBlock:
    def __init__(self, lines):
        self.lines= lines

class ListedLogicLine:
    def __init__(self,indent_lvl, variable, operator, assignment):
        self.indent_lvl= indent_lvl
        self.variable= variable
        self.operator= operator
        self.assignment = assignment

tmp_logical_block = LogicalBlock(
    lines= [
        ListedLogicLine(indent_lvl=1, variable="x", operator="=", assignment="15"),
        ListedLogicLine(indent_lvl=2, variable="guess", operator="=", assignment="x"),
        ListedLogicLine(indent_lvl=3, variable="guess", operator="+=", assignment="x"),
        ListedLogicLine(indent_lvl=6, variable="iter", operator="=", assignment="(guess + (guess / x)) / 2"),
    ]
)

def TranslateLogicalBlock(block : LogicalBlock):
    final_block = ""

    for line in block.lines:
        final_block += TranslateLogicalLine(line) + "\n"
    final_block += "}"

    return final_block
    

def TranslateLogicalLine(input_logical_line : ListedLogicLine) -> str:
    
    
    formatted_logic_block : str = ""
    formatted_logic_block = IndentLine(input_logical_line, formatted_logic_block)

    formatted_logic_block += (input_logical_line.variable + " "
    + input_logical_line.operator + " " + input_logical_line.assignment + ";")

    print(formatted_logic_block)
    return formatted_logic_block


def TranslateWholeFile():
    pass


#TranslateFieldDef(tmp_verison_field)
#TranslateProcDef(tmp_verison_procedure)
TranslateLogicalBlock(tmp_logical_block)