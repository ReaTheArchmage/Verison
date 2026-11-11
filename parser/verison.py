from enum import Enum, auto
import re
import field_parser
import procedure_parser
import logic_parser
import printer
from  ..translator import translator
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


class LineKind(Enum):
    """What a single (already-joined) line is, independent of where it
    sits structurally."""
    HEADER = auto()
    VAR = auto()
    CONST = auto()
    PROC_DECL = auto()
    LOGIC = auto()
    OTHER = auto()


class Frame:
    """One open, not-yet-closed container on the structural stack: either
    a proc block or a logic block (if/elif/else/for/while/match/nif/nfor/
    arm). `indent` is the indent level of the line that opened it;
    `entry` is the declaration dict that owns this frame's body."""
    def __init__(self, indent, entry, is_proc=False):
        self.indent = indent
        self.entry = entry
        self.is_proc = is_proc


class ParserState:
    def __init__(self):
        self.line_no = 0
        self.stack = []          # open Frames, innermost last
        self.declarations = []   # flat, ordered log of every parsed line
        self.errors = []

    def InProcBlock(self):
        return any(f.is_proc for f in self.stack)

    def CurrentProcName(self):
        """Name of the nearest enclosing proc, regardless of how many
        if/for/arm frames are nested in between."""
        for f in reversed(self.stack):
            if f.is_proc:
                return f.entry["name"]
        return None

    def CurrentContainer(self):
        """The body list of the innermost open block/proc, or None if
        nothing is currently open (true top level)."""
        for f in reversed(self.stack):
            if f.entry.get("body") is not None:
                return f.entry["body"]
        return None


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


def _CloseFramesIfDone(state, indent):
    """Pops every open frame whose header sits at or deeper than the
    current line's indent -- i.e. the current line is a sibling of (or
    outside) that frame, not nested inside it."""
    while state.stack and state.stack[-1].indent >= indent:
        state.stack.pop()


def _AppendEntry(state, entry):
    """Records entry in the flat declarations log, and -- if a block or
    proc is currently open -- also nests it under that block's body."""
    container = state.CurrentContainer()
    if container is not None:
        container.append(entry)
    state.declarations.append(entry)


def _HandleProcDecl(state, line, indent):
    if state.InProcBlock():
        state.errors.append(
            f"Line {state.line_no}: illegal nested procedure "
            f"declared inside '{state.CurrentProcName()}': {line.strip()!r}")
        return
    parsed = procedure_parser.ParseProcedureDeclaration(line)
    parsed["kind"] = "proc"
    parsed["line"] = state.line_no
    parsed["raw"] = line  # keep the original text for display
    parsed["body"] = []
    _AppendEntry(state, parsed)
    state.stack.append(Frame(indent=indent, entry=parsed, is_proc=True))


def _HandleField(state, line, kind):
    parsed = field_parser.ParseFieldDeclaration(line)
    parsed["kind"] = "var" if kind == LineKind.VAR else "const"
    parsed["line"] = state.line_no
    parsed["in_proc"] = state.CurrentProcName()
    parsed["raw"] = line  # keep the original text for display
    _AppendEntry(state, parsed)


def _HandleLogic(state, line, indent):
    parsed = logic_parser.ParseLogicLine(line)
    parsed["kind"] = "logic"
    parsed["line"] = state.line_no
    parsed["in_proc"] = state.CurrentProcName()
    parsed["raw"] = line
    _AppendEntry(state, parsed)
    # Every logic form except `return` can own a nested body -- open a
    # frame for it so subsequent, deeper-indented lines are captured.
    if parsed.get("body") is not None:
        state.stack.append(Frame(indent=indent, entry=parsed))


def UpdateState(state, line_no, line):
    state.line_no = line_no
    indent = CountIndent(line)

    _CloseFramesIfDone(state, indent)

    kind = ClassifyLine(line)
    if kind == LineKind.PROC_DECL:
        _HandleProcDecl(state, line, indent)
    elif kind in (LineKind.VAR, LineKind.CONST):
        _HandleField(state, line, kind)
    elif kind == LineKind.LOGIC:
        _HandleLogic(state, line, indent)
    return state


def ParseFile(path):
    state = ParserState()
    for line_no, line in ReadLogicalLines(path):
        UpdateState(state, line_no, line)
    return state


if __name__ == "__main__":
    import sys

    print_type = sys.argv[1] if len(sys.argv) > 1 else "-a"
    path       = "tests/field_procedure_syntax_test_1.verison"
    curr_state = ParseFile(path)
    printer.PrintParsedLines(curr_state, print_type)

    if curr_state.errors:
        print("Errors:")
        for err in curr_state.errors:
            print(f"  {err}")