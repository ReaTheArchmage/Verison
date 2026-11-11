from dataclasses import dataclass
from enum import Enum, auto
import re

try:
    from . import field_parser
    from . import procedure_parser
    from . import logic_parser
    from . import printer
except ImportError:
    # Running this file directly (python parser.py), not as part of the
    # `verison` package -- fall back to plain sibling imports.
    import field_parser
    import procedure_parser
    import logic_parser
    import printer

_DECLARATION_RE = re.compile(r"^\s*\(.*?\)\s*(\w+)")

# Plain assignment / operation statements, e.g. "x = 15" or "guess += x".
# These aren't declarations (field_parser's domain) or control-flow
# keywords (logic_parser's domain), so they're recognized here.
_ASSIGNMENT_RE = re.compile(r"^(\w+)\s*(\+=|-=|\*=|/=|%=|=)\s*(.+)$")


## ---------------------------------------------------------------------
## Translator input structures -- what ReformatForTranslator() emits.
## ---------------------------------------------------------------------

@dataclass
class ListedField:
    indent_lvl: int
    field: str
    name: str
    type_: str
    value: str


@dataclass
class ListedProcedure:
    field: str
    name: str
    returnType: str
    parameters: dict


@dataclass
class ListedLogicLine:
    indent_lvl: int
    variable: str
    operator: str
    assignment: str


@dataclass
class LogicalBlock:
    lines: list


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


def IsAssignmentLine(line):
    """'x = 15' / 'guess += x' -- a bare variable-operator-value
    statement, as opposed to a declaration or a control-flow keyword."""
    return _ASSIGNMENT_RE.match(line.strip()) is not None


def ParseAssignmentLine(line):
    """'x = 15' -> {"variable": "x", "operator": "=", "assignment": "15"}
    'guess += x' -> {"variable": "guess", "operator": "+=", "assignment": "x"}
    Caller must check IsAssignmentLine(line) first."""
    match = _ASSIGNMENT_RE.match(line.strip())
    return {"variable": match.group(1),
            "operator": match.group(2),
            "assignment": match.group(3).strip()}

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
    ASSIGNMENT = auto()
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
    if IsAssignmentLine(line):
        return LineKind.ASSIGNMENT
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


def _HandleAssignment(state, line):
    parsed = ParseAssignmentLine(line)
    parsed["kind"] = "assignment"
    parsed["line"] = state.line_no
    parsed["in_proc"] = state.CurrentProcName()
    parsed["raw"] = line
    _AppendEntry(state, parsed)


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
    elif kind == LineKind.ASSIGNMENT:
        _HandleAssignment(state, line)
    return state


def ParseFile(path):
    state = ParserState()
    for line_no, line in ReadLogicalLines(path):
        UpdateState(state, line_no, line)
    return state


## ---------------------------------------------------------------------
## Reformatting: turn parsed entries into the translator's input shapes.
## ---------------------------------------------------------------------

def ToListedField(entry):
    """Reformats a var/const entry (as produced by _HandleField) into a
    ListedField."""
    return ListedField(
        indent_lvl=CountIndent(entry["raw"]),
        field=entry["field"],
        name=entry["name"],
        type_=entry["type"],
        value=entry["value"],
    )


def SplitParameters(raw_params):
    """'x f32, steps i32' -> {"x": "f32", "steps": "i32"}"""
    params = {}
    if not raw_params:
        return params
    for piece in raw_params.split(","):
        piece = piece.strip()
        if not piece:
            continue
        name, _, type_ = piece.rpartition(" ")
        params[name.strip()] = type_.strip()
    return params


def ToListedProcedure(entry):
    """Reformats a proc entry (as produced by _HandleProcDecl) into a
    ListedProcedure."""
    return ListedProcedure(
        field=entry["kind"],  # always "proc"
        name=entry["name"],
        returnType=entry["return_type"],
        parameters=SplitParameters(entry["parameters"]),
    )


def ToListedLogicLine(entry):
    """Reformats an assignment entry (as produced by _HandleAssignment)
    into a ListedLogicLine."""
    return ListedLogicLine(
        indent_lvl=CountIndent(entry["raw"]),
        variable=entry["variable"],
        operator=entry["operator"],
        assignment=entry["assignment"],
    )


def ReformatForTranslator(entries):
    """Reformats a flat, ordered list of parsed entries (e.g.
    state.declarations, or one block's "body") into the translator's
    input structures: a ListedField for each var/const, a
    ListedProcedure for each proc signature, and a LogicalBlock for each
    run of consecutive assignment statements.

    Control-flow entries (if/elif/else/for/while/match/nif/nfor/return,
    match arms -- logic_parser's "logic" kind) have no translator
    structure defined yet, so they're passed through unchanged for now
    rather than silently dropped."""
    output = []
    pending = []

    def FlushPending():
        if pending:
            output.append(LogicalBlock(lines=list(pending)))
            pending.clear()

    for entry in entries:
        kind = entry.get("kind")
        if kind == "assignment":
            pending.append(ToListedLogicLine(entry))
        elif kind in ("var", "const"):
            FlushPending()
            output.append(ToListedField(entry))
        elif kind == "proc":
            FlushPending()
            output.append(ToListedProcedure(entry))
        else:
            FlushPending()
            output.append(entry)  # not yet covered -- see docstring

    FlushPending()
    return output


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