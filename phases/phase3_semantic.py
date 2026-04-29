"""Phase 3 – Semantic Analysis (ConciseLang v5)
   Output: Annotated Semantic Tree with types at every node
           + Scope / Symbol Table tree
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Any, Optional
from phase2_parser import *

# ── Scope ──────────────────────────────────────────────────────────────────
class Scope:
    def __init__(self, name: str, parent=None):
        self.name     = name
        self.parent   = parent
        self.symbols  = {}
        self.children = []
    def declare(self, name, typ): self.symbols[name] = typ
    def lookup(self, name):
        if name in self.symbols: return self.symbols[name]
        if self.parent:           return self.parent.lookup(name)
        return None
    def add_child(self, child): self.children.append(child); return child

# ── Annotated Node ─────────────────────────────────────────────────────────
@dataclass
class ANode:
    label    : str
    inferred : str
    scope    : str
    children : list = field(default_factory=list)

# ── Analyser ───────────────────────────────────────────────────────────────
class Analyzer:
    def __init__(self):
        self.root    = Scope("global")
        self.current = self.root
        self.funcs   = {}
        self.errors  = []
        for fn, ar in [("print",1),("reverse",1),("uppercase",1),
                       ("lowercase",1),("len",1),("abs",1),
                       ("str",1),("int",1),("float",1)]:
            self.funcs[fn] = (ar, "any")

    def push(self, name):
        child = Scope(name, self.current)
        self.current.add_child(child)
        self.current = child

    def pop(self): self.current = self.current.parent
    def declare(self, name, typ): self.current.declare(name, typ)
    def lookup(self, name):       return self.current.lookup(name)
    def error(self, msg):         self.errors.append(msg)

    def visit(self, node) -> ANode:
        return getattr(self, "visit_" + type(node).__name__, self._default)(node)

    def _default(self, node):
        return ANode(f"[{type(node).__name__}]", "any", self.current.name)

    def visit_Program(self, n):
        children = [self.visit(s) for s in n.stmts]
        return ANode("[PROGRAM]", "—", self.current.name, children)

    def visit_LetStmt(self, n):
        children = []
        for name, val in zip(n.names, n.values):
            an = self.visit(val)
            self.declare(name, an.inferred)
            an.label = f"[BIND '{name}' : {an.inferred}]  ← {an.label}"
            children.append(an)
        return ANode(f"[LET]  {n.names}", "—", self.current.name, children)

    def visit_FuncDecl(self, n):
        self.funcs[n.name] = (len(n.params), "inferred")
        self.push(f"func:{n.name}")
        for p in n.params: self.declare(p, "any")
        body_an = self.visit(n.body)
        ret = body_an.inferred
        self.pop()
        self.funcs[n.name] = (len(n.params), ret)
        self.declare(n.name, "func")
        body_an.label = f"(body) {body_an.label}"
        return ANode(
            f"[FUNC DECL '{n.name}']  params={n.params}  →  ret:{ret}",
            ret, self.current.name, [body_an])

    def visit_ForStmt(self, n):
        ts = self.visit(n.start); te = self.visit(n.end)
        if ts.inferred not in ("int","any") or te.inferred not in ("int","any"):
            self.error(f"for-range bounds must be int, got '{ts.inferred}'..'{te.inferred}'")
        self.push(f"for:{n.var}")
        self.declare(n.var, "int")
        body_nodes = [self.visit(s) for s in n.body]
        self.pop()
        ts.label = f"(start) {ts.label}"; te.label = f"(end) {te.label}"
        return ANode(
            f"[FOR LOOP]  var='{n.var}':int",
            "—", self.current.name, [ts, te] + body_nodes)

    def visit_WhileStmt(self, n):
        cond_an = self.visit(n.cond)
        if cond_an.inferred not in ("bool","any"):
            self.error(f"while-condition must be bool, got '{cond_an.inferred}'")
        self.push("while")
        body_nodes = [self.visit(s) for s in n.body]
        self.pop()
        cond_an.label = f"(cond) {cond_an.label}"
        return ANode(
            f"[WHILE LOOP]  cond:{cond_an.inferred}",
            "—", self.current.name, [cond_an] + body_nodes)

    def visit_SqlQuery(self, n):
        if self.lookup(n.source) is None:
            self.error(f"SQL 'from': undefined source '{n.source}'")
        self.push(f"sql:{n.source}")
        self.declare("n", "any")
        cond_an = None
        if n.cond:
            cond_an = self.visit(n.cond)
            cond_an.label = f"(where) {cond_an.label}"
        proj_an = self.visit(n.projection)
        proj_an.label = f"(select) {proj_an.label}"
        self.pop()
        children = ([cond_an] if cond_an else []) + [proj_an]
        return ANode(f"[SQL QUERY]  from='{n.source}'  →  list",
                     "list", self.current.name, children)

    def visit_PipeStmt(self, n):
        arg_nodes = [self.visit(a) for a in n.args]
        for i, an in enumerate(arg_nodes):
            an.label = f"(arg[{i}]) {an.label}"
        for fn in n.funcs:
            if fn == "print": continue
            if fn not in self.funcs and self.lookup(fn) is None:
                self.error(f"Pipe: undefined function '{fn}'")
        return ANode(f"[PIPE]  |> {' |> '.join(n.funcs)}",
                     "—", self.current.name, arg_nodes)

    def visit_ReturnStmt(self, n):
        an = self.visit(n.value)
        return ANode(f"[RETURN]  type:{an.inferred}", an.inferred,
                     self.current.name, [an])

    def visit_ExprStmt(self, n):
        if n.expr:
            an = self.visit(n.expr)
            return ANode(f"[EXPR STMT]  type:{an.inferred}",
                         an.inferred, self.current.name, [an])
        return ANode("[EXPR STMT]  (empty)", "void", self.current.name)

    def visit_IfExpr(self, n):
        c = self.visit(n.cond); t = self.visit(n.then); e = self.visit(n.else_)
        if c.inferred not in ("bool","any"):
            self.error(f"if-condition must be bool, got '{c.inferred}'")
        if t.inferred != e.inferred and "any" not in (t.inferred, e.inferred):
            self.error(f"if-branches type mismatch: '{t.inferred}' vs '{e.inferred}'")
        result_type = t.inferred if t.inferred != "any" else e.inferred
        c.label = f"(cond:{c.inferred}) {c.label}"
        t.label = f"(then:{t.inferred}) {t.label}"
        e.label = f"(else:{e.inferred}) {e.label}"
        return ANode(f"[IF EXPR]  → type:{result_type}",
                     result_type, self.current.name, [c, t, e])

    def visit_BinOp(self, n):
        l = self.visit(n.left); r = self.visit(n.right)
        if n.op in {"==","!=","<",">","<=",">=","in"}: typ = "bool"
        elif l.inferred == r.inferred == "int":         typ = "int"
        elif l.inferred == r.inferred == "float":       typ = "float"
        elif {l.inferred,r.inferred} == {"float","int"}:typ = "float"
        elif l.inferred == r.inferred == "str" and n.op=="+": typ = "str"
        else:                                            typ = "any"
        l.label = f"(L:{l.inferred}) {l.label}"
        r.label = f"(R:{r.inferred}) {r.label}"
        return ANode(f"[BIN OP '{n.op}']  → type:{typ}",
                     typ, self.current.name, [l, r])

    def visit_UnaryOp(self, n):
        an = self.visit(n.expr)
        if n.op == "-" and an.inferred not in ("int","float","any"):
            self.error(f"Unary '-' applied to '{an.inferred}'")
        return ANode(f"[UNARY '{n.op}']  → type:{an.inferred}",
                     an.inferred, self.current.name, [an])

    def visit_CallExpr(self, n):
        if n.name not in self.funcs and self.lookup(n.name) is None:
            self.error(f"Undefined function '{n.name}'")
        ret = "any"
        if n.name in self.funcs:
            arity, ret = self.funcs[n.name]
            if arity != len(n.args):
                self.error(f"'{n.name}' expects {arity} arg(s), got {len(n.args)}")
        arg_nodes = [self.visit(a) for a in n.args]
        for i, an in enumerate(arg_nodes):
            an.label = f"(arg[{i}]:{an.inferred}) {an.label}"
        return ANode(f"[CALL '{n.name}']  → type:{ret}",
                     ret, self.current.name, arg_nodes)

    def visit_Ident(self, n):
        t = self.lookup(n.name)
        if t is None: self.error(f"Undefined variable '{n.name}'"); t = "any"
        return ANode(f"[IDENT '{n.name}']  : {t}", t, self.current.name)

    def visit_IntLit(self, n):
        return ANode(f"[INT  {n.value}]  : int",   "int",   self.current.name)
    def visit_FloatLit(self, n):
        return ANode(f"[FLOAT  {n.value}]  : float","float", self.current.name)
    def visit_StrLit(self, n):
        return ANode(f'[STRING  "{n.value}"]  : str',"str",  self.current.name)
    def visit_BoolLit(self, n):
        v = "yes" if n.value else "no"
        return ANode(f"[BOOL  {v}]  : bool",        "bool",  self.current.name)
    def visit_ListLit(self, n):
        children = [self.visit(it) for it in n.items]
        return ANode(f"[LIST  ({len(n.items)} items)]  : list",
                     "list", self.current.name, children)


# ══════════════════════════════════════════════════════════════
#  Annotated Semantic Tree Printer
# ══════════════════════════════════════════════════════════════
def print_semantic_tree(anode: ANode, prefix: str = "", is_last: bool = True):
    connector = "└── " if is_last else "├── "
    print(prefix + connector + anode.label)
    child_prefix = prefix + ("    " if is_last else "│   ")
    for i, child in enumerate(anode.children):
        print_semantic_tree(child, child_prefix, i == len(anode.children)-1)

def print_scope_table(scope: Scope, prefix: str = "", is_last: bool = True):
    connector = "└── " if (prefix and is_last) else ("├── " if prefix else "")
    if scope.symbols:
        syms = ",  ".join(f"'{k}' : {v}" for k, v in scope.symbols.items())
    else:
        syms = "(empty)"
    print(f"  {prefix}{connector}[scope: {scope.name}]  →  {{ {syms} }}")
    child_prefix = prefix + ("    " if is_last else "│   ")
    for i, child in enumerate(scope.children):
        print_scope_table(child, child_prefix, i == len(scope.children)-1)

def run_semantic(ast):
    w = 62
    print("╔" + "═"*(w-2) + "╗")
    print("║  PHASE 3 ─── SEMANTIC ANALYSIS  (Annotated Tree)" + " "*(w-51) + "║")
    print("╚" + "═"*(w-2) + "╝\n")
    if ast is None:
        print("  ✘  Skipped (no AST).\n"); return None, None

    a = Analyzer()
    sem_tree = a.visit(ast)

    # ── Annotated Semantic Tree ───────────────────────────
    print("  Annotated Semantic Tree  (each node shows inferred type):")
    print("  " + "─"*56)
    print("  ROOT " + sem_tree.label)
    for i, child in enumerate(sem_tree.children):
        print_semantic_tree(child, "  ", i == len(sem_tree.children)-1)

    # ── Symbol / Scope Table ──────────────────────────────
    print()
    print("  Symbol Table  (scope tree):")
    print("  " + "─"*56)
    print_scope_table(a.root)

    if a.errors:
        print(f"\n  ✘  {len(a.errors)} semantic error(s) found:")
        for e in a.errors: print(f"    • {e}")
        print(); return None, a

    print(f"\n  ✔  Semantic check passed — no errors.\n")
    return ast, a