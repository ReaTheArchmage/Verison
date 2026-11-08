import re

LOGIC_KEYWORDS = ("if", "elif", "else", "match", "for", "while", "return", "nif", "nfor")
# TODO: nif & nfor parsing returns None for all values, because their dedicated logic is missing.
# if/elif/match/for/while all carry their payload in a parenthesized
# clause after an optional colon; only these get a "condition" pulled out.
_CONDITION_FORMS = ("if", "elif", "match", "for", "while")
_HEAD_RE = re.compile(r"^(\w+)\s*:?\s*(.*)$")
_ARM_RE = re.compile(r"^(\w+)\*\s*(.*)$")


def FindLogicKeyword(line):
    match = _HEAD_RE.match(line)
    if match and match.group(1) in LOGIC_KEYWORDS:
        return match.group(1)
    return None


def FindArmLabel(line):
    """Match-arm lines look like `true* //logic` or `false* //logic`."""
    match = _ARM_RE.match(line)
    return match.group(1) if match else None


def FindCondition(line):
    """Pulls the parenthesized clause out of an if/elif/match/for/while
    header, e.g. "for : (i32 x, i in 0.<4)" -> "i32 x, i in 0.<4"."""
    start = line.find("(")
    end = line.rfind(")")
    if start == -1 or end == -1 or end <= start:
        return None
    return line[start + 1:end]


def FindReturnValue(line):
    """Everything after the 'return' keyword, or None for a bare return
    (the named-return form, where the value was already assigned)."""
    match = _HEAD_RE.match(line)
    if not match or match.group(1) != "return":
        return None
    value = match.group(2).strip()
    return value or None


def IsLogicLine(line):
    stripped = line.strip()
    return FindLogicKeyword(stripped) is not None or FindArmLabel(stripped) is not None


def ParseLogicLine(line):
    line = line.strip()

    arm_label = FindArmLabel(line)
    if arm_label is not None:
        return {"form": "arm", "label": arm_label, "condition": None,
                "value": None, "body": []}

    keyword = FindLogicKeyword(line)

    if keyword == "return":
        return {"form": "return", "label": None, "condition": None,
                "value": FindReturnValue(line), "body": None}

    condition = FindCondition(line) if keyword in _CONDITION_FORMS else None
    return {"form": keyword, "label": None, "condition": condition,
            "value": None, "body": []}