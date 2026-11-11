import re

try:
    from ..parser import parser
except ImportError:
    # Running this file directly (python translator.py), not as part of
    # the `verison` package -- fall back to loading parser.py from its
    # sibling directory instead.
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "parser"))
    import parser

class ListedField:
    def __init__(
        self, indent_lvl,field, name, type_, value): 
        
        self.indent_lvl = indent_lvl
        self.field = field
        self.name = name
        self.type_ = type_
        self.value = value


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

    #print(formatted_field)
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

    #print(formatted_procedure)
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


def TranslateLogicalBlock(block : LogicalBlock):
    final_block = ""

    for line in block.lines:
        final_block += TranslateLogicalLine(line) + "\n"

    return final_block.rstrip("\n")
    

def TranslateLogicalLine(input_logical_line : ListedLogicLine) -> str:
    
    
    formatted_logic_block : str = ""
    formatted_logic_block = IndentLine(input_logical_line, formatted_logic_block)

    formatted_logic_block += (input_logical_line.variable + " "
    + input_logical_line.operator + " " + input_logical_line.assignment + ";")

    #print(formatted_logic_block)
    return formatted_logic_block


# INPUT TESTS:

tmp_verison_field = ListedField(
    indent_lvl= 2,
    field= "var", name= "title",
    type_= "&str", value= '"Verison"'
)
tmp_verison_procedure = ListedProcedure(
    field= "proc",
    name= "squareRoot",
    returnType="()",
    parameters={"x" : "f32", "steps" : "i32"}
)
tmp_logical_block = LogicalBlock(
    lines= [
        ListedLogicLine(indent_lvl=1, variable="x", operator="=", assignment="15"),
        ListedLogicLine(indent_lvl=1, variable="guess", operator="=", assignment="x"),
        ListedLogicLine(indent_lvl=1, variable="guess", operator="+=", assignment="x"),
        ListedLogicLine(indent_lvl=1, variable="iter", operator="=", assignment="(guess + (guess / x)) / 2"),
    ]
)

#TranslateFieldDef(tmp_verison_field)
#TranslateProcDef(tmp_verison_procedure)
#TranslateLogicalBlock(tmp_logical_block)


## ---------------------------------------------------------------------
## Driver: parser module -> nested Rust source, control flow included.
## ---------------------------------------------------------------------
# Walks the parser's *nested* entries (state.root, recursing into each
# entry's own "body") rather than the old flat declarations list, so
# every if/elif/else/while/for opens exactly one brace and closes
# exactly one brace -- no more stray "}" from treating every block the
# same as a proc body.

# Verison's word-form conditionals ("is true", "and", "or", "not",
# "inverse") aren't valid Rust; symbol forms (&&, ||, !, <, >=...) already
# are, so they pass through untouched. Best-effort, not exhaustive.
_COND_REPLACEMENTS = (
    (" and ", " && "), (" or ", " || "),
    ("inverse ", "!"), ("not ", "!"),
    (" is true", ""), (" == true", ""),
)

def TranslateCondition(condition: str) -> str:
    cond = f" {condition.strip()} "
    for old, new in _COND_REPLACEMENTS:
        cond = cond.replace(old, new)
    return cond.strip()


# Only the range form -- "i32 x, i in 0.<4" -- is handled. The
# collection form ("String x, i in [String;4]") and match/nif/nfor are
# passed through as a visible TODO rather than guessed at.
_FOR_RANGE_RE = re.compile(r"^\s*\w+\s+(\w+)\s*,\s*(\w+)\s+in\s+(.+?)\.<(.+?)\s*$")

def TranslateForHeader(condition: str) -> str:
    match = _FOR_RANGE_RE.match(condition)
    if not match:
        return None
    value_name, index_name, start, end = match.groups()
    return (f"for ({index_name.strip()}, {value_name.strip()}) "
            f"in ({start.strip()}..{end.strip()}).enumerate()")


def EntryIndent(entry) -> int:
    return parser.CountIndent(entry.get("raw", ""))


def TranslateLogicEntry(entry) -> str:
    """One if/elif/else/while/for/return entry (parser's "logic" kind),
    recursing into its body so nesting and braces come out balanced."""
    indent = "\t" * EntryIndent(entry)
    form = entry.get("form")

    if form == "return":
        value = entry.get("value")
        return f"{indent}return{(' ' + value) if value else ''};"

    if form in ("if", "elif", "while"):
        keyword = "else if" if form == "elif" else form
        cond = TranslateCondition(entry.get("condition") or "")
        body = TranslateBody(entry.get("body") or [])
        return f"{indent}{keyword} {cond} {{\n{body}\n{indent}}}"

    if form == "else":
        body = TranslateBody(entry.get("body") or [])
        return f"{indent}else {{\n{body}\n{indent}}}"

    if form == "for":
        header = TranslateForHeader(entry.get("condition") or "")
        if header is None:
            raw = entry.get("raw", "").strip()
            return f"{indent}// TODO: no Rust translation yet for: {raw}"
        body = TranslateBody(entry.get("body") or [])
        return f"{indent}{header} {{\n{body}\n{indent}}}"

    # match / nif / nfor / arm -- logic_parser doesn't fully parse these
    # yet either (see its own TODO), so there's nothing to translate.
    raw = entry.get("raw", "").strip()
    return f"{indent}// TODO: no Rust translation yet for: {raw}"


def TranslateProc(entry) -> str:
    header = TranslateProcDef(parser.ToListedProcedure(entry))  # ends with " {"
    body = TranslateBody(entry.get("body") or [])
    return f"{header}\n{body}\n}}"


def TranslateBody(entries) -> str:
    """Recursively translates a list of parser entries (a proc's body,
    a block's body, or the file's top level) into Rust text. Consecutive
    plain assignments are grouped into one LogicalBlock, matching how
    the translator's own data shapes expect them."""
    lines = []
    pending = []

    def FlushPending():
        if pending:
            lines.append(TranslateLogicalBlock(LogicalBlock(lines=list(pending))))
            pending.clear()

    for entry in entries:
        kind = entry.get("kind")
        if kind == "assignment":
            pending.append(parser.ToListedLogicLine(entry))
            continue

        FlushPending()
        if kind in ("var", "const"):
            lines.append(TranslateFieldDef(parser.ToListedField(entry)))
        elif kind == "proc":
            lines.append(TranslateProc(entry))
        elif kind == "logic":
            lines.append(TranslateLogicEntry(entry))
        else:
            raw = entry.get("raw", "").strip()
            lines.append(f"// TODO: no Rust translation yet for: {raw}")

    FlushPending()
    return "\n".join(lines)


def TranslateFile(path: str) -> str:
    """Parses `path`, then recursively translates its top-level entries
    (and everything nested under them) into a single Rust source string."""
    state = parser.ParseFile(path)
    return TranslateBody(state.root)


def PrintTranslatedFile(path: str) -> None:
    """Quick driver: translates `path` and prints the resulting Rust
    source file."""
    print(TranslateFile(path))


if __name__ == "__main__":
    import sys

    # Adjust this default to wherever your .verison test files live.
    path = sys.argv[1] if len(sys.argv) > 1 else "../parser/tests/field_procedure_syntax_test_1.verison"
    PrintTranslatedFile(path)