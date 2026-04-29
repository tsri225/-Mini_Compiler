"""Phase 5 – Code Optimization (ConciseLang v5)"""
from __future__ import annotations
from phase4_irgen import TACInstr
from typing import List

ARITH={"+":lambda a,b:a+b,"-":lambda a,b:a-b,"*":lambda a,b:a*b,
       "/":lambda a,b:a/b,"%":lambda a,b:a%b,
       "<":lambda a,b:int(a<b),">":lambda a,b:int(a>b),
       "<=":lambda a,b:int(a<=b),">=":lambda a,b:int(a>=b),
       "==":lambda a,b:int(a==b),"!=":lambda a,b:int(a!=b)}

def _is_num(v):
    try: float(v); return True
    except: return False

def constant_fold(instrs):
    out=[]; n=0
    for ins in instrs:
        if ins.op in ARITH and _is_num(ins.arg1) and _is_num(ins.arg2):
            r=ARITH[ins.op](float(ins.arg1),float(ins.arg2))
            r=int(r) if isinstance(r,float) and r==int(r) else r
            new=TACInstr("COPY",dest=ins.dest,arg1=str(r))
            print(f"  [Fold]      {str(ins).strip()}")
            print(f"              → {str(new).strip()}")
            out.append(new); n+=1
        else: out.append(ins)
    if not n: print("  (no constant folds applied)")
    return out

def copy_propagate(instrs):
    env={}; out=[]; n=0
    def res(v): return env.get(v,v)
    for ins in instrs:
        if ins.op=="COPY" and not _is_num(ins.dest):
            resolved=res(ins.arg1)
            if resolved!=ins.dest:
                env[ins.dest]=resolved
                print(f"  [Copy-prop] {ins.dest}  →  {resolved}"); n+=1
            out.append(TACInstr("COPY",dest=ins.dest,arg1=resolved))
        else:
            out.append(TACInstr(ins.op,dest=ins.dest,
                                arg1=res(ins.arg1),arg2=res(ins.arg2)))
    if not n: print("  (no copy propagations applied)")
    return out

def dead_code_elim(instrs):
    used=set()
    for ins in instrs:
        if ins.arg1: used.add(ins.arg1)
        if ins.arg2: used.add(ins.arg2)
    out=[]; n=0
    for ins in instrs:
        if ins.op=="COPY" and ins.dest.startswith("t") and ins.dest not in used:
            print(f"  [DCE]       Removed dead: {str(ins).strip()}"); n+=1; continue
        out.append(ins)
    if not n: print("  (no dead code eliminated)")
    return out

def run_optimizer(instrs):
    w=62
    print("╔"+"═"*(w-2)+"╗")
    print("║  PHASE 5 ─── CODE OPTIMIZATION"+" "*(w-32)+"║")
    print("╚"+"═"*(w-2)+"╝\n")
    if instrs is None: print("  ✘  Skipped.\n"); return None
    print("  Pass 1 — Constant Folding\n  "+"─"*56)
    instrs=constant_fold(instrs)
    print("\n  Pass 2 — Copy Propagation\n  "+"─"*56)
    instrs=copy_propagate(instrs)
    print("\n  Pass 3 — Dead Code Elimination\n  "+"─"*56)
    instrs=dead_code_elim(instrs)
    print(f"\n  Optimized IR ({len(instrs)} instruction(s)):\n  "+"─"*56)
    for i in instrs: print(i)
    print(f"\n  ✔  Optimization complete.\n")
    return instrs