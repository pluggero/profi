#!/usr/bin/env python3
import argparse
import random
import re
import sys
from pathlib import Path

VBA_KEYWORDS = {
    "and",
    "as",
    "boolean",
    "byref",
    "byte",
    "byval",
    "call",
    "case",
    "cbool",
    "cbyte",
    "ccur",
    "cdate",
    "cdbl",
    "cdec",
    "chr",
    "chrw",
    "cint",
    "clng",
    "const",
    "csng",
    "cstr",
    "currency",
    "date",
    "declare",
    "dim",
    "do",
    "double",
    "each",
    "else",
    "elseif",
    "empty",
    "end",
    "eqv",
    "erase",
    "error",
    "event",
    "exit",
    "false",
    "for",
    "friend",
    "function",
    "get",
    "global",
    "gosub",
    "goto",
    "if",
    "imp",
    "implements",
    "in",
    "integer",
    "is",
    "len",
    "let",
    "lib",
    "like",
    "long",
    "loop",
    "me",
    "mod",
    "new",
    "next",
    "nothing",
    "null",
    "object",
    "on",
    "option",
    "optional",
    "or",
    "preserve",
    "private",
    "property",
    "public",
    "raiseevent",
    "redim",
    "resume",
    "return",
    "select",
    "set",
    "single",
    "static",
    "step",
    "stop",
    "string",
    "sub",
    "then",
    "to",
    "true",
    "type",
    "typeof",
    "until",
    "variant",
    "wend",
    "while",
    "with",
    "withevents",
    "xor",
    # common COM / built-ins we must not rename
    "getobject",
    "createobject",
    "shell",
    "environ",
    "array",
    "lbound",
    "ubound",
    "mid",
    "left",
    "right",
    "asc",
    "replace",
    "split",
    "join",
    "trim",
    "ltrim",
    "rtrim",
    "ucase",
    "lcase",
    "instr",
    "strreverse",
    "sleep",
    "application",
    "activedocument",
    "thisworkbook",
    "workbooks",
    "documents",
    "vba",
    "debug",
    "print",
    "msgbox",
    "autoopen",
    "document_open",
    "auto_open",
    "workbook_open",
    "value",
}

IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")
STRING_RE = re.compile(r'"((?:[^"]|"")*)"')
INT_RE = re.compile(r"(?<![A-Za-z0-9_.])(\d+)(?![A-Za-z0-9_.])")
COMMENT_RE = re.compile(r"(?m)(^|\s)'[^\n]*")


def rand_name(rng, length=None):
    length = length or rng.randint(4, 7)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    first = rng.choice(alphabet)
    rest = "".join(rng.choice(alphabet + "0123456789") for _ in range(length - 1))
    return first + rest


def strip_comments(src):
    lines = []
    for line in src.splitlines():
        in_str = False
        out = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == '"':
                in_str = not in_str
                out.append(ch)
            elif ch == "'" and not in_str:
                break
            else:
                out.append(ch)
            i += 1
        stripped = "".join(out).rstrip()
        if stripped:
            lines.append(stripped)
    # Remove `Rem` comments too
    return "\n".join(l for l in lines if not re.match(r"^\s*Rem\b", l, re.I))


def collect_identifiers(src):
    """Find user-defined Sub / Function / Dim names worth renaming."""
    names = set()
    for m in re.finditer(
        r"(?im)^\s*(?:Public\s+|Private\s+)?Sub\s+([A-Za-z_]\w*)", src
    ):
        names.add(m.group(1))
    for m in re.finditer(
        r"(?im)^\s*(?:Public\s+|Private\s+)?Function\s+([A-Za-z_]\w*)", src
    ):
        names.add(m.group(1))
    for m in re.finditer(
        r"(?im)^\s*(?:Public\s+|Private\s+)?(?:Sub|Function)\s+[A-Za-z_]\w*\s*\(([^)]*)\)",
        src,
    ):
        for param in m.group(1).split(","):
            param = re.sub(r"(?i)\b(ByVal|ByRef)\b", "", param).strip()
            param = re.sub(r"(?i)\s+As\s+\w+.*$", "", param).strip()
            if re.match(r"^[A-Za-z_]\w*$", param):
                names.add(param)
    for m in re.finditer(r"(?im)\bDim\s+([A-Za-z_]\w*)", src):
        names.add(m.group(1))
    # Locally-assigned (implicit) variables: `foo = ...`
    for m in re.finditer(r"(?m)^\s*([A-Za-z_]\w*)\s*=", src):
        names.add(m.group(1))
    # Call targets on their own line: `MyMacro` or `Call MyMacro`
    for m in re.finditer(r"(?im)^\s*Call\s+([A-Za-z_]\w*)", src):
        names.add(m.group(1))
    # Filter out keywords / built-ins
    return {n for n in names if n.lower() not in VBA_KEYWORDS}


def rename_identifiers(src, rng):
    targets = collect_identifiers(src)
    mapping = {t: rand_name(rng) for t in targets}
    # Don't rename `AutoOpen`
    for k in list(mapping):
        if k.lower() in {"autoopen", "auto_open", "document_open", "workbook_open"}:
            mapping.pop(k)

    def replace_outside_strings(line):
        parts = re.split(r'("(?:[^"]|"")*")', line)
        for i, part in enumerate(parts):
            if i % 2 == 1:  # inside a quoted string
                continue

            def sub(m):
                return mapping.get(m.group(1), m.group(1))

            parts[i] = IDENT_RE.sub(sub, part)
        return "".join(parts)

    return "\n".join(replace_outside_strings(l) for l in src.splitlines()), mapping


def encode_string(literal, randint):
    """
    Encode every character into a 3-digit zero-padded decimal (like VBA pad to length 3).
    Example: 'A' -> '065'
    """
    output = ""
    for ch in literal:
        # In PS the char is cast to byte then added 17, so get the codepoint (0-255) then add 17
        val = (ord(ch) & 0xFF) + randint
        s = str(val)
        # pad to 3 digits
        if len(s) == 1:
            s = "00" + s
        elif len(s) == 2:
            s = "0" + s
        output += s
    return f'DePuzzle("{output}")'


def obfuscate_strings(src, randint):
    out_lines = []
    for line in src.splitlines():
        # Split on strings so we only rewrite the literal parts
        parts = re.split(r'("(?:[^"]|"")*")', line)
        for i, part in enumerate(parts):
            if i % 2 == 1:
                inner = part[1:-1]
                if inner == "" or inner == '""':
                    parts[i] = '""'
                else:
                    parts[i] = encode_string(inner, randint)
        out_lines.append("".join(parts))

    return "\n".join(out_lines)


def make_junk_line(rng):
    name = rand_name(rng)
    kind = rng.choice(["int", "str", "bool", "math"])
    if kind == "int":
        return f"Dim {name} : {name} = {rng.randint(1000, 99999)}"
    if kind == "str":
        filler = "".join(
            rng.choice("abcdefghijklmnop") for _ in range(rng.randint(4, 10))
        )
        return f'Dim {name} : {name} = "{filler}"'
    if kind == "bool":
        return f"Dim {name} : {name} = ({rng.randint(1, 9)} > {rng.randint(1, 9)})"
    a, b = rng.randint(10, 999), rng.randint(10, 999)
    return f"Dim {name} : {name} = ({a} Xor {b})"


def inject_junk(src, rng, count):
    """Sprinkle `count` junk statements inside Sub bodies."""
    lines = src.splitlines()
    # Find indices that are inside a Sub/Function body (between header and End)
    inside = [False] * len(lines)
    depth = 0
    for i, line in enumerate(lines):
        if re.match(r"(?i)^\s*(Public\s+|Private\s+)?(Sub|Function)\b", line):
            depth += 1
            continue
        if re.match(r"(?i)^\s*End\s+(Sub|Function)\b", line):
            depth -= 1
            continue
        if depth > 0:
            inside[i] = True

    eligible = [i for i, ok in enumerate(inside) if ok]
    if not eligible:
        return src

    for _ in range(count):
        idx = rng.choice(eligible)
        junk = make_junk_line(rng)
        lines.insert(idx, junk)
        # Re-index eligible positions (cheap: shift everything >= idx)
        eligible = [(i + 1) if i >= idx else i for i in eligible]
        eligible.append(idx)
    return "\n".join(lines)


def get_decode(randint):
    DECODE = f"""
Function Boerne(Beets)
    Boerne = Chr(Beets - {randint})
End Function

Function Erdbeere(Grapes)
    Erdbeere = Left(Grapes, 3)
End Function

Function Mandel(Jelly)
    Mandel = Right(Jelly, Len(Jelly) - 3)
End Function

Function DePuzzle(Milk)
    Do While Len(Milk) > 0
    MM = MM + Boerne(Erdbeere(Milk))
    Milk = Mandel(Milk)
    Loop
    DePuzzle = MM
End Function
"""
    return DECODE


def obfuscate(src, rng, junk_count):
    randint = rng.randint(1, 20)
    src = get_decode(randint) + src
    src = strip_comments(src)
    src = obfuscate_strings(src, randint)
    src, _ = rename_identifiers(src, rng)
    # src = inject_junk(src, rng, junk_count)
    return src


def main():
    ap = argparse.ArgumentParser(description="Obfuscate a plaintext VBA macro.")
    ap.add_argument("input", type=Path, help="Input .vb / .vba / .bas file")
    ap.add_argument(
        "-o", "--output", type=Path, help="Output file (default: <input>_obf.<ext>)"
    )
    ap.add_argument(
        "--seed", type=int, default=None, help="RNG seed for reproducibility"
    )
    ap.add_argument(
        "--junk", type=int, default=6, help="Number of junk lines to inject"
    )
    args = ap.parse_args()

    rng = random.Random(args.seed)
    src = args.input.read_text()
    result = obfuscate(src, rng, args.junk)

    out = args.output or args.input.with_name(
        f"{args.input.stem}_obf{args.input.suffix}"
    )
    out.write_text(result)
    print(f"[+] Wrote {len(result)} bytes to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
