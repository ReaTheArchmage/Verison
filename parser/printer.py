def _SummarizeCell(value):
    """Collapse nested structures into something a one-line table cell
    can hold. `body` now holds a list of child declaration dicts (after
    the parser fix) -- show their line numbers instead of dumping the
    dicts themselves, since each child already gets its own row."""
    if isinstance(value, list):
        if not value:
            return ""
        if isinstance(value[0], dict):
            lines = [str(child.get("line", "?")) for child in value]
            return "lines " + ",".join(lines)
        return str(value)
    return value


def PrintParsedLines(state, debug_type):
    if not state.declarations:
        print("No declarations found.")
        return

    rows = []

    for decl in state.declarations:
        row = {}

        if debug_type in ("-a", "-s"):
            row["raw"] = decl.get("raw", "")

        if debug_type in ("-a", "-p"):
            row.update({
                k: _SummarizeCell(v)
                for k, v in decl.items()
                if k != "raw"
            })

        rows.append(row)

    # Collect all column names
    columns = list(dict.fromkeys(
        key for row in rows for key in row
    ))

    # Calculate column widths
    widths = {
        col: max(
            len(col),
            max((len(str(row.get(col, ""))) for row in rows), default=0)
        )
        for col in columns
    }

    def separator():
        return "+" + "+".join("-" * (widths[col] + 2) for col in columns) + "+"

    def format_row(row):
        return "|" + "|".join(
            f" {str(row.get(col, '')):<{widths[col]}} "
            for col in columns
        ) + "|"

    print("\nParsed Declarations:")
    print(separator())
    print(format_row({col: col for col in columns}))
    print(separator())

    for row in rows:
        print(format_row(row))

    print(separator())
    print(f"\nTotal declarations: {len(rows)}")


def DebugPrint(debug_type, raw, pretty):
    if debug_type == "-a":
        print(raw)
        print(pretty)
    elif debug_type == "-p":
        print(pretty)
    elif debug_type == "-s":
        print(raw)