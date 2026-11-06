import re

# Matches the declaration-keyword position only: the first word immediately
# following the closing parenthesis of the leading (type) annotation, e.g.
#   (i32)var x : 1          -> "var"
#   (i32)proc : myProc(...) -> "proc"
# var / const / proc are only ever legal as declarations in that position.
# Any other occurrence of those words on the line (identifiers, string
# values, comments, etc.) is deliberately NOT matched.
DECLARATION_RE = re.compile(r"^\s*\(.*?\)\s*(\w+)")


def FindDeclarationKeyword(line):
    match = DECLARATION_RE.match(line)
    if not match:
        return None, -1
    return match.group(1), match.start(1)


def CountIndent(line):
    """Indentation level as an unsigned int, counted strictly in leading
    tab characters. Spaces do not count toward indentation."""
    indent = 0
    for ch in line:
        if ch != "\t":
            break
        indent += 1
    return indent