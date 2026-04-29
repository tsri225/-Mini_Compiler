"""Phase 4 – Intermediate Code Generation / 3-Address Code (ConciseLang v5)"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from phase2_parser import *

@dataclass
class TACInstr:
    op:str; dest:str=""; arg1:str=""; arg2:str=""
    def __str__(self):
        if self.op=="LABEL":     return f"{self.dest}:"
        if self.op=="GOTO":      return f"    GOTO         {self.dest}"
        if self.op=="IFFALSE":   return f"    IFFALSE      {self.arg1}  →  GOTO {self.dest}"
        if self.op=="PARAM":     return f"    PARAM        {self.arg1}"
        if self.op=="CALL":      return f"    {self.dest:<10} = CALL {self.arg1} ({self.arg2} arg)"
        if self.op=="RETURN":    return f"    RETURN       {self.arg1}"
        if self.op=="PRINT":     return f"    PRINT        {self.arg1}"
        if self.op=="COPY":      return f"    {self.dest:<10} = {self.arg1}"
        if self.op=="FUNC":      return f"\nFUNC {self.dest}:"
        if self.op=="ENDFUNC":   return f"ENDFUNC {self.dest}"
        if self.op=="ITER_INIT": return f"    ITER_INIT    {self.dest}  ←  list({self.arg1})"
        if self.op=="ITER_NEXT": return f"    ITER_NEXT    {self.dest}  or GOTO {self.arg2}"
        if self.op=="FILTER":    return f"    FILTER       {self.dest}  ←  {self.arg1}"
        if self.op=="PROJECT":   return f"    PROJECT      {self.dest}  ←  {self.arg1}"
        if self.arg2: return f"    {self.dest:<10} = {self.arg1}  {self.op}  {self.arg2}"
        return         f"    {self.dest:<10} = {self.op} {self.arg1}"

class IRGen:
    def __init__(self): self.instrs=[]; self.tc=0; self.lc=0
    def tmp(self): self.tc+=1; return f"t{self.tc}"
    def lbl(self): self.lc+=1; return f"L{self.lc}"
    def emit(self,*a,**kw): self.instrs.append(TACInstr(*a,**kw))
    def gen(self,node): return getattr(self,"gen_"+type(node).__name__,lambda n:"")(node)
    def gen_Program(self,n):
        for s in n.stmts: self.gen(s)
    def gen_LetStmt(self,n):
        for name,val in zip(n.names,n.values):
            v=self.gen(val); self.emit("COPY",dest=name,arg1=v)
    def gen_FuncDecl(self,n):
        self.emit("FUNC",dest=n.name)
        for p in n.params: self.emit("PARAM",arg1=p)
        ret=self.gen(n.body); self.emit("RETURN",arg1=ret); self.emit("ENDFUNC",dest=n.name)
    def gen_ForStmt(self,n):
        s=self.gen(n.start); e=self.gen(n.end)
        self.emit("COPY",dest=n.var,arg1=s)
        ls,le=self.lbl(),self.lbl()
        self.emit("LABEL",dest=ls); t=self.tmp()
        self.emit("<",dest=t,arg1=n.var,arg2=e)
        self.emit("IFFALSE",dest=le,arg1=t)
        for stmt in n.body: self.gen(stmt)
        t2=self.tmp(); self.emit("+",dest=t2,arg1=n.var,arg2="1")
        self.emit("COPY",dest=n.var,arg1=t2)
        self.emit("GOTO",dest=ls); self.emit("LABEL",dest=le)
    def gen_WhileStmt(self,n):
        lt,le=self.lbl(),self.lbl()
        self.emit("LABEL",dest=lt); cond=self.gen(n.cond)
        self.emit("IFFALSE",dest=le,arg1=cond)
        for stmt in n.body: self.gen(stmt)
        self.emit("GOTO",dest=lt); self.emit("LABEL",dest=le)
    def gen_SqlQuery(self,n):
        it=self.tmp(); item=self.tmp(); res=self.tmp()
        ll,le=self.lbl(),self.lbl()
        self.emit("ITER_INIT",dest=it,arg1=n.source)
        self.emit("COPY",dest=res,arg1="[]")
        self.emit("LABEL",dest=ll)
        self.emit("ITER_NEXT",dest=item,arg1=it,arg2=le)
        if n.cond:
            cval=self.gen(n.cond); tf=self.tmp()
            self.emit("FILTER",dest=tf,arg1=cval)
            self.emit("IFFALSE",dest=ll,arg1=tf)
        proj=self.gen(n.projection); self.emit("PROJECT",dest=res,arg1=proj)
        self.emit("GOTO",dest=ll); self.emit("LABEL",dest=le); return res
    def gen_PipeStmt(self,n):
        for a in n.args: self.emit("PARAM",arg1=self.gen(a))
        fn0=n.funcs[0]
        if fn0=="print":
            v=self.gen(n.args[0]) if len(n.args)==1 else "args"
            self.emit("PRINT",arg1=v); return
        t=self.tmp(); self.emit("CALL",dest=t,arg1=fn0,arg2=str(len(n.args)))
        for fn in n.funcs[1:]:
            if fn=="print": self.emit("PRINT",arg1=t); return
            self.emit("PARAM",arg1=t); t2=self.tmp()
            self.emit("CALL",dest=t2,arg1=fn,arg2="1"); t=t2
        self.emit("PRINT",arg1=t)
    def gen_ExprStmt(self,n):
        if n.expr: self.gen(n.expr)
    def gen_ReturnStmt(self,n):
        v=self.gen(n.value); self.emit("RETURN",arg1=v); return v
    def gen_IfExpr(self,n):
        cond=self.gen(n.cond); le,lend=self.lbl(),self.lbl(); res=self.tmp()
        self.emit("IFFALSE",dest=le,arg1=cond)
        tv=self.gen(n.then); self.emit("COPY",dest=res,arg1=tv)
        self.emit("GOTO",dest=lend); self.emit("LABEL",dest=le)
        fv=self.gen(n.else_); self.emit("COPY",dest=res,arg1=fv)
        self.emit("LABEL",dest=lend); return res
    def gen_BinOp(self,n):
        l=self.gen(n.left); r=self.gen(n.right); t=self.tmp()
        self.emit(n.op,dest=t,arg1=l,arg2=r); return t
    def gen_UnaryOp(self,n):
        v=self.gen(n.expr); t=self.tmp(); self.emit("NEG",dest=t,arg1=v); return t
    def gen_CallExpr(self,n):
        for a in n.args: self.emit("PARAM",arg1=self.gen(a))
        t=self.tmp(); self.emit("CALL",dest=t,arg1=n.name,arg2=str(len(n.args))); return t
    def gen_Ident(self,n):    return n.name
    def gen_IntLit(self,n):   return str(n.value)
    def gen_FloatLit(self,n): return str(n.value)
    def gen_StrLit(self,n):   return f'"{n.value}"'
    def gen_BoolLit(self,n):  return "1" if n.value else "0"
    def gen_ListLit(self,n):
        items=[self.gen(it) for it in n.items]; t=self.tmp()
        self.emit("COPY",dest=t,arg1=f"[{', '.join(items)}]"); return t

def run_irgen(ast):
    w=62
    print("╔"+"═"*(w-2)+"╗")
    print("║  PHASE 4 ─── INTERMEDIATE CODE GENERATION  (TAC)"+" "*(w-52)+"║")
    print("╚"+"═"*(w-2)+"╝\n")
    if ast is None: print("  ✘  Skipped.\n"); return None
    g=IRGen(); g.gen(ast)
    for ins in g.instrs: print(ins)
    print(f"\n  ✔  IR generated — {len(g.instrs)} instruction(s).\n")
    return g.instrs