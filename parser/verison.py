import field_parser
import procedure_parser

# Verison language keyword lists (v0.1)

TYPE_KEYWORDS = [
    "u32",
    "i32",
    "f32",
    "bool",
    "char",
    "String",
    "&str",
]

FLOW_CONTROLS = [
    "if",
    "elif",
    "else",
    "match",
    "for",
    "while",
    "continue",
    "break",
    "nif",
    "nfor",
]

# GOALS:
#   .Have a unified input that takes one file only.
#   .Have it translated into primitive Rust.
#   .Understand how to format and structure an entire project as a rust project.
#   .Make boilerplate to directly pipe it to cargo.

"""      -TEMP-      """

# A written test for the parser modules, they are independent for now,
# and act on two different files. The scope is to use the same file
# for both parsing and then reassembly the code structure at translate-time.

def TmpParseTest():

    tmp_proc_test  =  "tests/procedure_syntax_test.verison"
    tmp_field_test =  "tests/field_syntax_test.verison"

    print("{\n")
    curr_fields =     field_parser.     OpenFile (tmp_field_test)
    print("\n} PARSED FIELD DECLARATIONS\n\n")    
    print("{\n")
    curr_procedures = procedure_parser. OpenFile (tmp_proc_test)
    print("\n} PARSED PROCEDURE DECLARATIONS \n\n")

TmpParseTest()

#we need to find the first occurence of var,const or proc in  the line
#to asses the state of the current line.

