"""Phase 2 – Syntax Analysis / Recursive Descent Parser (ConciseLang v5)
   Output: ASCII Syntax Tree with box-drawing characters │ ├── └──
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Any, Optional

# ── AST Nodes ──────────────────────────────────────────────────────────────
@dataclass
class Program:    stmts: List[Any]
@dataclass
class LetStmt:    names: List[str]; values: List[Any]
@dataclass
class FuncDecl:   name: str; params: List[str]; body: Any
@dataclass
class ForStmt:    start: Any; end: Any; var: str; body: List[Any]
@dataclass
class WhileStmt:  cond: Any; body: List[Any]
@dataclass
class SqlQuery:   source: str; cond: Optional[Any]; projection: Any
@dataclass
class PipeStmt:   args: List[Any]; funcs: List[str]
@dataclass
class ReturnStmt: value: Any
@dataclass
class ExprStmt:   expr: Any
@dataclass
class IfExpr:     cond: Any; then: Any; else_: Any
@dataclass
class BinOp:      op: str; left: Any; right: Any
@dataclass
class UnaryOp:    op: str; expr: Any
@dataclass
class CallExpr:   name: str; args: List[Any]
@dataclass
class Ident:      name: str
@dataclass
class IntLit:     value: int
@dataclass
class FloatLit:   value: float
@dataclass
class StrLit:     value: str
@dataclass
class BoolLit:    value: bool
@dataclass
class ListLit:    items: List[Any]

class ParseError(Exception):
    def __init__(self, msg, line):
        super().__init__(f"[Parse Error] Line {line}: {msg}")

# token types valid as pipe target names
_NAME_TYPES = {"IDENT","PRINT","RETURN","REVERSE","UPPERCASE","LOWERCASE","LEN","ABS"}

class Parser:
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.type != "NEWLINE"]
        self.pos = 0

    def peek(self):           return self.tokens[self.pos]
    def check(self, *types):  return self.peek().type in types
    def advance(self):
        t = self.tokens[self.pos]
        if t.type != "EOF": self.pos += 1
        return t
    def expect(self, tp):
        t = self.peek()
        if t.type != tp:
            raise ParseError(f"Expected '{tp}' but got '{t.type}'({t.value!r})", t.line)
        return self.advance()
    def match(self, *types):
        if self.peek().type in types: return self.advance()
        return None
    def expect_name(self):
        """Accept IDENT or any keyword used as a function name (e.g. print)."""
        t = self.peek()
        if t.type in _NAME_TYPES or t.type == "IDENT":
            return self.advance()
        raise ParseError(f"Expected function name, got '{t.type}'({t.value!r})", t.line)

    def parse(self) -> Program:
        stmts = []
        while self.match("SEMI"): pass
        while not self.check("EOF"):
            stmts.append(self.stmt())
            while self.match("SEMI"): pass
        return Program(stmts)

    def stmt(self):
        t = self.peek()
        if t.type == "LET":            return self.let_stmt()
        if t.type in ("FUNC","FN"):    return self.func_decl()
        if t.type == "FOR":            return self.for_stmt()
        if t.type == "WHILE":          return self.while_stmt()
        if t.type == "FROM":           return self.sql_query()
        if t.type == "RETURN":
            self.advance(); return ReturnStmt(self.expr())
        return self.expr_or_pipe_stmt()

    def let_stmt(self):
        self.expect("LET")
        names = [self.expect("IDENT").value]
        while self.match("COMMA"): names.append(self.expect("IDENT").value)
        self.expect("ASSIGN")
        values = [self.expr()]
        for _ in names[1:]: self.expect("COMMA"); values.append(self.expr())
        return LetStmt(names, values)

    def func_decl(self):
        self.advance()
        name = self.expect("IDENT").value; params = []
        if self.match("LPAREN"):
            while not self.check("RPAREN","EOF"):
                params.append(self.expect("IDENT").value); self.match("COMMA")
            self.expect("RPAREN")
        self.expect("LBRACE"); body = self.expr(); self.expect("RBRACE")
        return FuncDecl(name, params, body)

    def for_stmt(self):
        self.expect("FOR"); start = self.primary()
        self.expect("DOTDOT"); end = self.primary()
        self.expect("AS"); var = self.expect("IDENT").value
        self.expect("LBRACE"); body = []
        while self.match("SEMI"): pass
        while not self.check("RBRACE","EOF"):
            body.append(self.stmt())
            while self.match("SEMI"): pass
        self.expect("RBRACE")
        return ForStmt(start, end, var, body)

    def while_stmt(self):
        self.expect("WHILE"); self.expect("LPAREN")
        cond = self.expr(); self.expect("RPAREN")
        self.expect("LBRACE"); body = []
        while self.match("SEMI"): pass
        while not self.check("RBRACE","EOF"):
            body.append(self.stmt())
            while self.match("SEMI"): pass
        self.expect("RBRACE")
        return WhileStmt(cond, body)

    def sql_query(self):
        self.expect("FROM"); source = self.expect("IDENT").value; cond = None
        if self.match("WHERE"): cond = self.compare()
        self.expect("SELECT"); projection = self.expr()
        return SqlQuery(source, cond, projection)

    def expr_or_pipe_stmt(self):
        first = self.expr(); args = [first]
        while self.check("COMMA"): self.advance(); args.append(self.expr())
        if self.check("PIPE"):
            funcs = []
            while self.match("PIPE"): funcs.append(self.expect_name().value)
            return PipeStmt(args, funcs)
        return ExprStmt(first)

    def expr(self):
        if self.check("IF"): return self.if_expr()
        return self.compare()

    def compare(self):
        left = self.addexpr()
        op = self.match("EQ","NEQ","LT","GT","LEQ","GEQ","IN")
        if op: return BinOp(op.value, left, self.addexpr())
        return left

    def addexpr(self):
        left = self.mulexpr()
        while True:
            op = self.match("PLUS","MINUS")
            if not op: break
            left = BinOp(op.value, left, self.mulexpr())
        return left

    def mulexpr(self):
        left = self.unary()
        while True:
            op = self.match("STAR","SLASH","MOD")
            if not op: break
            left = BinOp(op.value, left, self.unary())
        return left

    def unary(self):
        op = self.match("MINUS","NOT")
        if op: return UnaryOp(op.value, self.unary())
        return self.primary()

    def primary(self):
        t = self.peek()
        if t.type == "IF":       return self.if_expr()
        if t.type == "INTEGER":  self.advance(); return IntLit(int(t.value))
        if t.type == "FLOAT":    self.advance(); return FloatLit(float(t.value))
        if t.type == "STRING":   self.advance(); return StrLit(t.value[1:-1])
        if t.type == "YES":      self.advance(); return BoolLit(True)
        if t.type == "NO":       self.advance(); return BoolLit(False)
        if t.type == "LBRACKET": return self.list_lit()
        if t.type == "LPAREN":
            self.advance(); e = self.expr(); self.expect("RPAREN"); return e
        if t.type == "IDENT":
            self.advance()
            if self.check("LPAREN"):
                self.advance(); args = []
                while not self.check("RPAREN","EOF"):
                    args.append(self.expr()); self.match("COMMA")
                self.expect("RPAREN"); return CallExpr(t.value, args)
            return Ident(t.value)
        raise ParseError(f"Unexpected token '{t.type}'({t.value!r})", t.line)

    def if_expr(self):
        self.expect("IF"); self.expect("LPAREN")
        cond = self.expr(); self.expect("RPAREN")
        then = self.expr(); self.expect("ELSE"); else_ = self.expr()
        return IfExpr(cond, then, else_)

    def list_lit(self):
        self.expect("LBRACKET"); items = []
        while not self.check("RBRACKET","EOF"):
            items.append(self.expr()); self.match("COMMA")
        self.expect("RBRACKET"); return ListLit(items)


# ══════════════════════════════════════════════════════════════
#  ASCII Syntax Tree Printer  (box-drawing: │  ├──  └──)
# ══════════════════════════════════════════════════════════════
def _node_label(node) -> str:
    if isinstance(node, Program):    return f"[PROGRAM]  ({len(node.stmts)} statements)"
    if isinstance(node, LetStmt):    return f"[LET]  names={node.names}"
    if isinstance(node, FuncDecl):   return f"[FUNC DECL]  '{node.name}'  params={node.params}"
    if isinstance(node, ForStmt):    return f"[FOR LOOP]  var='{node.var}'"
    if isinstance(node, WhileStmt):  return f"[WHILE LOOP]"
    if isinstance(node, SqlQuery):   return f"[SQL QUERY]  from='{node.source}'"
    if isinstance(node, PipeStmt):   return f"[PIPE]  |> {' |> '.join(node.funcs)}"
    if isinstance(node, ReturnStmt): return f"[RETURN]"
    if isinstance(node, ExprStmt):   return f"[EXPR STMT]"
    if isinstance(node, IfExpr):     return f"[IF EXPR]"
    if isinstance(node, BinOp):      return f"[BIN OP  '{node.op}']"
    if isinstance(node, UnaryOp):    return f"[UNARY OP  '{node.op}']"
    if isinstance(node, CallExpr):   return f"[CALL]  '{node.name}'  ({len(node.args)} args)"
    if isinstance(node, Ident):      return f"[IDENT]  '{node.name}'"
    if isinstance(node, IntLit):     return f"[INT]  {node.value}"
    if isinstance(node, FloatLit):   return f"[FLOAT]  {node.value}"
    if isinstance(node, StrLit):     return f'[STRING]  "{node.value}"'
    if isinstance(node, BoolLit):    return f"[BOOL]  {'yes' if node.value else 'no'}"
    if isinstance(node, ListLit):    return f"[LIST]  ({len(node.items)} items)"
    return f"[{type(node).__name__}]"

def _children(node):
    if isinstance(node, Program):
        return [(f"stmt[{i}]", s) for i, s in enumerate(node.stmts)]
    if isinstance(node, LetStmt):
        return [(f"bind '{nm}'", val) for nm, val in zip(node.names, node.values)]
    if isinstance(node, FuncDecl):
        return [("body", node.body)]
    if isinstance(node, ForStmt):
        ch = [("start", node.start), ("end", node.end)]
        for i, s in enumerate(node.body): ch.append((f"body[{i}]", s))
        return ch
    if isinstance(node, WhileStmt):
        ch = [("cond", node.cond)]
        for i, s in enumerate(node.body): ch.append((f"body[{i}]", s))
        return ch
    if isinstance(node, SqlQuery):
        ch = []
        if node.cond: ch.append(("where", node.cond))
        ch.append(("select", node.projection))
        return ch
    if isinstance(node, PipeStmt):
        return [(f"arg[{i}]", a) for i, a in enumerate(node.args)]
    if isinstance(node, ReturnStmt):
        return [("value", node.value)]
    if isinstance(node, ExprStmt):
        return [("expr", node.expr)] if node.expr else []
    if isinstance(node, IfExpr):
        return [("cond", node.cond), ("then", node.then), ("else", node.else_)]
    if isinstance(node, BinOp):
        return [("left", node.left), ("right", node.right)]
    if isinstance(node, UnaryOp):
        return [("operand", node.expr)]
    if isinstance(node, CallExpr):
        return [(f"arg[{i}]", a) for i, a in enumerate(node.args)]
    if isinstance(node, ListLit):
        return [(f"item[{i}]", it) for i, it in enumerate(node.items)]
    return []

def print_tree(node, prefix: str = "", is_last: bool = True, edge_label: str = ""):
    connector = "└── " if is_last else "├── "
    label_str  = (f"({edge_label}) " if edge_label else "") + _node_label(node)
    print(prefix + connector + label_str)
    child_prefix = prefix + ("    " if is_last else "│   ")
    children = _children(node)
    for i, (lbl, child) in enumerate(children):
        last = (i == len(children) - 1)
        print_tree(child, child_prefix, last, lbl)

def run_parser(tokens):
    w = 62
    print("╔" + "═"*(w-2) + "╗")
    print("║  PHASE 2 ─── SYNTAX ANALYSIS  (Syntax Tree)" + " "*(w-46) + "║")
    print("╚" + "═"*(w-2) + "╝\n")
    try:
        ast = Parser(tokens).parse()
        print("  Syntax Tree:")
        print("  " + "─"*56)
        print("  ROOT")
        children = _children(ast)
        for i, (lbl, child) in enumerate(children):
            last = (i == len(children)-1)
            print_tree(child, "  ", last, lbl)
        print(f"\n  ✔  Parsing complete — AST built successfully.\n")
        return ast
    except ParseError as e:
        print(f"\n  ✘  {e}\n"); return None