"""Phase 1 – Lexical Analysis (ConciseLang v5)"""
import re
from dataclasses import dataclass
from typing import List

@dataclass
class Token:
    type: str
    value: str
    line: int

class LexerError(Exception):
    def __init__(self, msg, line):
        super().__init__(f"[Lexer Error] Line {line}: {msg}")

KEYWORDS = {
    "let","func","fn","for","while","from","where","select",
    "as","if","else","return","print","yes","no","and","or","not","in"
}

TOKEN_SPECS = [
    ("COMMENT",  r"#[^\n]*"),
    ("NEWLINE",  r"\n"),
    ("SKIP",     r"[ \t\r]+"),
    ("FLOAT",    r"\d+\.\d+"),
    ("INTEGER",  r"\d+"),
    ("PIPE",     r"\|>"),
    ("DOTDOT",   r"\.\."),
    ("LBRACE",   r"\{"),
    ("RBRACE",   r"\}"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("LBRACKET", r"\["),
    ("RBRACKET", r"\]"),
    ("COMMA",    r","),
    ("SEMI",     r";"),
    ("EQ",       r"=="),
    ("NEQ",      r"!="),
    ("LEQ",      r"<="),
    ("GEQ",      r">="),
    ("LT",       r"<"),
    ("GT",       r">"),
    ("ASSIGN",   r"="),
    ("PLUS",     r"\+"),
    ("MINUS",    r"-"),
    ("STAR",     r"\*"),
    ("SLASH",    r"/"),
    ("MOD",      r"%"),
    ("IDENT",    r"[A-Za-z_][A-Za-z0-9_]*"),
]
_STRING_PAT = re.compile(r'"[^"\n]*"')

def tokenize(source: str) -> List[Token]:
    compiled = [(n, re.compile(p)) for n, p in TOKEN_SPECS]
    tokens: List[Token] = []
    line = 1; pos = 0
    while pos < len(source):
        m = _STRING_PAT.match(source, pos)
        if m:
            tokens.append(Token("STRING", m.group(), line))
            pos = m.end(); continue
        matched = False
        for name, pat in compiled:
            m = pat.match(source, pos)
            if not m: continue
            val = m.group()
            if name == "NEWLINE":
                tokens.append(Token("NEWLINE", "\\n", line)); line += 1
            elif name == "IDENT" and val in KEYWORDS:
                tokens.append(Token(val.upper(), val, line))
            elif name not in ("SKIP", "COMMENT"):
                tokens.append(Token(name, val, line))
            pos = m.end(); matched = True; break
        if not matched:
            raise LexerError(f"Unexpected character {source[pos]!r}", line)
    tokens.append(Token("EOF", "", line))
    return tokens

def run_lexer(source: str):
    w = 62
    print("╔" + "═"*(w-2) + "╗")
    print("║  PHASE 1 ─── LEXICAL ANALYSIS" + " "*(w-32) + "║")
    print("╚" + "═"*(w-2) + "╝\n")
    try:
        tokens = tokenize(source)
        visible = [t for t in tokens if t.type not in ("NEWLINE","EOF")]
        print(f"  {'#':<5} {'TOKEN TYPE':<16} {'VALUE':<30} LINE")
        print(f"  {'─'*5} {'─'*16} {'─'*30} {'─'*4}")
        for i, t in enumerate(visible, 1):
            print(f"  {i:<5} {t.type:<16} {t.value!r:<30} {t.line}")
        print(f"\n  ✔  Lexing complete — {len(visible)} tokens produced.\n")
        return tokens
    except LexerError as e:
        print(f"\n  ✘  {e}\n"); return None