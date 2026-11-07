from enum import Enum, auto
import re
import field_parser
import procedure_parser
import logic_parser

_DECLARATION_RE = re.compile(r"^\s*\(.*?\)\s*(\w+)")

def CountIndent(line):
    """Indentation level as an unsigned int. Each leading tab counts as
    one indent level; every run of 4 leading spaces counts as one more
    (a partial run of fewer than 4 trailing spaces doesn't round up)."""
    indent = 0
    space_run = 0
    for ch in line:
        if ch == "\t":
            indent += 1
            space_run = 0
        elif ch == " ":
            space_run += 1
            if space_run == 4:
                indent += 1
                space_run = 0
        else:
            break
    return indent

def FindDeclarationKeyword(line):
    """Matches the declaration-keyword position only: the first word
    immediately following the closing parenthesis of the leading (type)
    annotation, e.g.
        (i32)var x : 1          -> "var"
        (i32)proc : myProc(...) -> "proc"
    Returns (keyword, char_index) or (None, -1). var/const/proc elsewhere
    on the line (identifiers, values, comments...) are deliberately not
    matched."""
    match = _DECLARATION_RE.match(line)
    if not match:
        return None, -1
    return match.group(1), match.start(1)

_OPEN_TO_CLOSE = {"(": ")", "[": "]", "{": "}"}
_CLOSERS = set(_OPEN_TO_CLOSE.values())

def IsBalanced(text):
    """True once every bracket/paren/brace opened in text is also closed."""
    stack = []
    for ch in text:
        if ch in _OPEN_TO_CLOSE:
            stack.append(_OPEN_TO_CLOSE[ch])
        elif ch in _CLOSERS:
            if not stack or stack.pop() != ch:
                return False
    return not stack

def ReadLogicalLines(path):
    """Yields (line_no, text) pairs. Physical lines are merged whenever a
    bracket/paren/brace opened on one of them isn't closed yet, so array
    literals, parameter lists and conditions may freely span several
    physical lines. line_no is the physical line the logical line started
    on; blank lines and full-line comments are dropped before a logical
    line has started."""
    with open(path, "r") as f:
        pending = ""
        start_no = 0
        for line_no, raw in enumerate(f, start=1):
            text = raw.rstrip("\n")

            if not pending:
                stripped = text.strip()
                if not stripped or stripped.startswith("//"):
                    continue
                start_no = line_no
                pending = text
            else:
                pending += " " + text.strip()

            if IsBalanced(pending):
                yield start_no, pending
                pending = ""

        if pending.strip():
            yield start_no, pending

class Context(Enum):
    """Persistent structural context, carried from line to line."""
    TOP_LEVEL = auto()
    PROC_BLOCK = auto()

class LineKind(Enum):
    """What a single (already-joined) line is, independent of where it
    sits structurally."""
    VAR = auto()
    CONST = auto()
    PROC_DECL = auto()
    LOGIC = auto()
    OTHER = auto()

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

def ClassifyLine(line):
    keyword, _ = FindDeclarationKeyword(line)
    if keyword == "proc":
        return LineKind.PROC_DECL
    if keyword == "const":
        return LineKind.CONST
    if keyword == "var":
        return LineKind.VAR
    if logic_parser.IsLogicLine(line):
        return LineKind.LOGIC
    return LineKind.OTHER

def _CloseProcBlockIfDone(state, indent):
    if state.InProcBlock() and indent <= state.proc_indent:
        state.context = Context.TOP_LEVEL
        state.proc_indent = None
        state.proc_name = None

def _HandleProcDecl(state, line, indent):
    if state.InProcBlock():
        state.errors.append(
            f"Line {state.line_no}: illegal nested procedure "
            f"declared inside '{state.proc_name}': {line.strip()!r}")
        return
    parsed = procedure_parser.ParseProcedureDeclaration(line)
    parsed["kind"] = "proc"
    parsed["line"] = state.line_no
    parsed["raw"] = line  # keep the original text for display
    state.declarations.append(parsed)
    state.context = Context.PROC_BLOCK
    state.proc_indent = indent
    state.proc_name = parsed["name"]

def _HandleField(state, line, kind):
    parsed = field_parser.ParseField(line)
    parsed["kind"] = "var" if kind == LineKind.VAR else "const"
    parsed["line"] = state.line_no
    parsed["in_proc"] = state.proc_name if state.InProcBlock() else None
    parsed["raw"] = line  # keep the original text for display
    state.declarations.append(parsed)

def _HandleLogic(state, line):
    parsed = logic_parser.ParseLogicLine(line)
    parsed["kind"] = "logic"
    parsed["line"] = state.line_no
    parsed["in_proc"] = state.proc_name if state.InProcBlock() else None
    parsed["raw"] = line
    state.declarations.append(parsed)

def UpdateState(state, line_no, line):
    state.line_no = line_no
    indent = CountIndent(line)

    _CloseProcBlockIfDone(state, indent)

    kind = ClassifyLine(line)
    if kind == LineKind.PROC_DECL:
        _HandleProcDecl(state, line, indent)
    elif kind in (LineKind.VAR, LineKind.CONST):
        _HandleField(state, line, kind)
    elif kind == LineKind.LOGIC:
        _HandleLogic(state, line)
    return state

def ParseFile(path):
    state = ParserState()
    for line_no, line in ReadLogicalLines(path):
        UpdateState(state, line_no, line)
    return state

def PrintParsedLines(state, debug_type):
    for decl in state.declarations:
        raw = decl.get("raw", "")
        fields = {k: v for k, v in decl.items() if k != "raw"}
        pretty = ", ".join(f"{k}={v!r}" for k, v in fields.items())
        DebugPrint(debug_type, raw, pretty)

def DebugPrint(debug_type, raw, pretty):
    if debug_type == "-a":
        print(raw)
        print(pretty)
    elif debug_type == "-p":
        print(pretty)
    elif debug_type == "-s":
        print(raw)

if __name__ == "__main__":
    import sys

    print_type = sys.argv[1] if len(sys.argv) > 1 else "-a"
    path       = "tests/procedure_syntax_test.verison"
    curr_state = ParseFile(path)
    PrintParsedLines(curr_state, print_type)

    if curr_state.errors:
        print("Errors:")
        for err in curr_state.errors:
            print(f"  {err}")