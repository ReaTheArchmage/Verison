from enum import Enum, auto
import parser_common
import field_parser
import procedure_parser

class Context(Enum):
    TOP_LEVEL = auto()
    VAR = auto()
    CONST = auto()
    PROC_DECL = auto()
    PROC_BLOCK = auto()


class ParserState:
    def __init__(self):
        self.context = Context.TOP_LEVEL
        self.line_no = 0

        # tracks the proc currently "open", if any
        self.proc_indent = None
        self.proc_name = None

        self.declarations = []
        self.errors = []

    def InProcBlock(self):
        return self.context == Context.PROC_BLOCK


def GetIndent(line):
    return parser_common.CountIndent(line)


def ClassifyLine(line):
    keyword, _ = parser_common.FindDeclarationKeyword(line)

    if keyword == procedure_parser.proc:
        return Context.PROC_DECL
    if keyword == field_parser.const:
        return Context.CONST
    if keyword == field_parser.var:
        return Context.VAR
    return Context.TOP_LEVEL

def UpdateState(state, line):
    state.line_no += 1
    stripped = line.strip()
    if not stripped or stripped.startswith("//"):
        return state

    indent = GetIndent(line)
    kind = ClassifyLine(line)

    if state.context == Context.PROC_BLOCK and indent <= state.proc_indent:
        state.context = Context.TOP_LEVEL
        state.proc_indent = None
        state.proc_name = None

    if kind == Context.PROC_DECL:
        if state.InProcBlock():
            state.errors.append(
                f"Line {state.line_no}: illegal nested procedure "
                f"declared inside '{state.proc_name}': {stripped!r}")
            return state

        parsed = procedure_parser.ParseProcedureDeclaration(line)
        parsed["kind"] = "proc"
        parsed["line"] = state.line_no
        parsed["raw"] = line  # keep the original text for display
        state.declarations.append(parsed)

        state.context = Context.PROC_BLOCK
        state.proc_indent = indent
        state.proc_name = parsed["name"]
        return state

    if kind in (Context.VAR, Context.CONST):
        parsed = field_parser.ParseField(line)
        parsed["kind"] = "var" if kind == Context.VAR else "const"
        parsed["line"] = state.line_no
        parsed["in_proc"] = state.proc_name if state.InProcBlock() else None
        parsed["raw"] = line  # keep the original text for display
        state.declarations.append(parsed)
        return state

    return state

def ParseFile(path):
    state = ParserState()
    with open(path, "r") as f:
        for line in f:
            UpdateState(state, line.rstrip("\n"))
    return state

def PrintParsedLines(state):
    """Prints each declaration: the original source line, then its
    parsed dict laid out horizontally on the line below, with a
    blank-line spacer between entries."""
    for decl in state.declarations:
        raw = decl.get("raw", "")
        fields = {k: v for k, v in decl.items() if k != "raw"}
        pretty = ", ".join(f"{k}={v!r}" for k, v in fields.items())

        print(raw)
        print(pretty)
        print()

if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "tests/field_procedure_syntax_test.verison"
    curr_state = ParseFile(path)
    PrintParsedLines(curr_state)

    if curr_state.errors:
        print("Errors:")
        for err in curr_state.errors:
            print(f"  {err}")