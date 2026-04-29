"""
Phase 6 – Target Code Generation (pseudo-assembly)  (ConciseLang v4)
"""
from __future__ import annotations
from phase4_irgen import TACInstr
from typing import List

class CodeGen:
    def __init__(self): self.asm=[]; self.regs={}; self.rc=0
    def alloc(self, name=None):
        self.rc+=1; r=f"R{self.rc}"
        if name: self.regs[name]=r
        return r
    def reg(self, v): return self.regs.get(v, v)
    def emit(self, s): self.asm.append(s)

    def generate(self, instrs):
        self.emit("; ── ConciseLang v4 Assembly ─────────────────────────────")
        self.emit(".section .data")
        self.emit(".section .text")
        self.emit(".global _start")
        self.emit("_start:")
        for ins in instrs:
            self.emit(f"  ; {ins}")
            op = ins.op
            if op == "FUNC":
                self.emit(f"\n{ins.dest}:")
                self.emit(f"  PUSH  FP"); self.emit(f"  MOV   FP, SP")
            elif op == "ENDFUNC":
                self.emit(f"  MOV   SP, FP"); self.emit(f"  POP   FP"); self.emit(f"  RET")
            elif op == "LABEL":
                self.emit(f"\n{ins.dest}:")
            elif op == "COPY":
                r = self.alloc(ins.dest)
                self.emit(f"  MOV   {r}, {self.reg(ins.arg1)}")
            elif op in {"+","-","*","/","%"}:
                r1=self.reg(ins.arg1); r2=self.reg(ins.arg2); rd=self.alloc(ins.dest)
                mn={"+":"ADD","-":"SUB","*":"MUL","/":"DIV","%":"MOD"}[op]
                self.emit(f"  MOV   {rd}, {r1}"); self.emit(f"  {mn:<5} {rd}, {r2}")
            elif op in {"<",">","<=",">=","==","!="}:
                r1=self.reg(ins.arg1); r2=self.reg(ins.arg2); rd=self.alloc(ins.dest)
                self.emit(f"  CMP   {r1}, {r2}")
                fl={"<":"LT",">":"GT","<=":"LE",">=":"GE","==":"EQ","!=":"NE"}[op]
                self.emit(f"  SET{fl} {rd}")
            elif op == "IFFALSE":
                self.emit(f"  JZ    {self.reg(ins.arg1)}, {ins.dest}")
            elif op == "GOTO":
                self.emit(f"  JMP   {ins.dest}")
            elif op == "PARAM":
                self.emit(f"  PUSH  {self.reg(ins.arg1)}")
            elif op == "CALL":
                rd=self.alloc(ins.dest)
                self.emit(f"  CALL  {ins.arg1}"); self.emit(f"  MOV   {rd}, ACC")
            elif op == "RETURN":
                self.emit(f"  MOV   ACC, {self.reg(ins.arg1)}"); self.emit(f"  RET")
            elif op == "PRINT":
                self.emit(f"  PUSH  {self.reg(ins.arg1)}")
                self.emit(f"  SYSCALL  sys_print"); self.emit(f"  POP   ACC")
            elif op == "NEG":
                rd=self.alloc(ins.dest)
                self.emit(f"  MOV   {rd}, {self.reg(ins.arg1)}"); self.emit(f"  NEG   {rd}")
            elif op == "ITER_INIT":
                rd=self.alloc(ins.dest)
                self.emit(f"  LEA   {rd}, [{self.reg(ins.arg1)}]")
                self.emit(f"  MOV   {ins.dest}_IDX, 0")
            elif op == "ITER_NEXT":
                rd=self.alloc(ins.dest)
                self.emit(f"  LOAD  {rd}, [{self.reg(ins.arg1)}+{ins.dest}_IDX]")
                self.emit(f"  INC   {ins.dest}_IDX")
                self.emit(f"  JGE   {ins.dest}_IDX, LEN({self.reg(ins.arg1)}), {ins.arg2}")
            elif op == "FILTER":
                rd=self.alloc(ins.dest); self.emit(f"  FILT  {rd}, {self.reg(ins.arg1)}")
            elif op == "PROJECT":
                rd=self.alloc(ins.dest); self.emit(f"  PROJ  {rd}, {self.reg(ins.arg1)}")
        self.emit("  HALT")

def run_codegen(instrs):
    print("╔" + "═"*62 + "╗")
    print("║  PHASE 6 – TARGET CODE GENERATION (Assembly)" + " "*16 + "║")
    print("╚" + "═"*62 + "╝\n")
    if instrs is None: print("  ✘  Skipped."); return None
    cg = CodeGen(); cg.generate(instrs)
    for line in cg.asm: print(line)
    print(f"\n  ✔  Code generation complete – {len(cg.asm)} assembly line(s).")
    return cg.asm, cg.regs