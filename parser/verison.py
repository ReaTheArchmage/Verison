import field_parser
from   field_parser import FindFieldDef
from   field_parser import FindName
from   field_parser import FindType
from   field_parser import FindValue

def CountLines(file) -> int:
    with open(file, "r") as f:
        line_count = sum(1 for line in f)   
    return line_count

def TranslateField(line):
    f_idx, field = FindFieldDef(line)
    type_ = FindType(line, f_idx)
    d_idx, value = FindValue(line)
    name = FindName(line, d_idx)
    
    listed_line = [
        field,name,type_,value,
        ]
    Translate(listed_line)

    print(
        "initial line:", line.rstrip("\n"),
        "\n---\n",
        "field:", field, "\n",
        "type:", type_, "\n",
        "value:", value, "\n",
        "name:", name, "\n",
    )

def TranslateFieldsToRust(file_path, lines, show_skipped=False):
    count = 0
    with open(file_path, 'r') as f:
        for line in f:
            stripped = line.strip()
            # Skip blank lines and full-line comments
            if stripped == "" or stripped.startswith("//"):
                if show_skipped:
                    print(line.rstrip("\n"))
                continue
            if count >= lines:
                break
            TranslateField(line)
            count += 1

def Translate(listed_line):
    
    final_rust_line = ""
    ver_field = listed_line[0] 
    if ver_field == field_parser.var:
        final_rust_line += field_parser.rust_var + " "
    elif ver_field == field_parser.const:
        final_rust_line += field_parser.const + " "
    ver_name = listed_line[1]
    final_rust_line += ver_name + " :"
    ver_type = listed_line[2]
    final_rust_line += " " + ver_type
    ver_value = listed_line[3]
    final_rust_line += " = " + ver_value

    print( final_rust_line + ";")
    return final_rust_line + ";"

#TranslateFieldsToRust(
    #field_parser.file_path, CountLines(field_parser.file_path), True)
