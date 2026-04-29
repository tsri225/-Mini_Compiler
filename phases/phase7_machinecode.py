"""Phase 7 – Machine Code Generation / Hex Encoding (ConciseLang v5)"""
from __future__ import annotations
from typing import List

OPCODES={"MOV":0x01,"ADD":0x02,"SUB":0x03,"MUL":0x04,"DIV":0x05,"MOD":0x06,
         "CMP":0x07,"SETLT":0x08,"SETGT":0x09,"SETLE":0x0A,"SETGE":0x0B,
         "SETEQ":0x0C,"SETNE":0x0D,"JMP":0x10,"JZ":0x11,"CALL":0x12,
         "RET":0x13,"PUSH":0x14,"POP":0x15,"NEG":0x1A,"SYSCALL":0x20,
         "LEA":0x21,"LOAD":0x22,"INC":0x23,"JGE":0x24,"FILT":0x25,
         "PROJ":0x26,"HALT":0xFF}

def _enc(op):
    if op.startswith("R"):
        try: return int(op[1:])
        except: pass
    try: return int(float(op))&0xFF
    except: return sum(ord(c) for c in op)&0xFF

def assemble(asm_lines):
    labels={}; addr=0
    for line in asm_lines:
        s=line.strip()
        if not s or s.startswith(";") or s.startswith("."): continue
        if s.endswith(":") and " " not in s: labels[s[:-1]]=addr
        else: addr+=1
    machine=[]
    for line in asm_lines:
        s=line.strip()
        if not s or s.startswith(";") or s.startswith(".") or \
           (s.endswith(":") and " " not in s): continue
        if ";" in s: s=s[:s.index(";")].strip()
        if not s: continue
        parts=s.replace(","," ").split()
        mn=parts[0].upper(); opcode=OPCODES.get(mn,0x00)
        ops=[labels[p]&0xFF if p in labels else _enc(p) for p in parts[1:]]
        byte_seq=[opcode,len(ops)]+ops[:2]
        while len(byte_seq)<4: byte_seq.append(0x00)
        hex_str=" ".join(f"0x{b:02X}" for b in byte_seq[:4])
        machine.append(f"  {hex_str:<40}  ; {parts[0]:<10} {' '.join(parts[1:])}")
    return machine

def run_machinecode(asm_data):
    w=62
    print("╔"+"═"*(w-2)+"╗")
    print("║  PHASE 7 ─── MACHINE CODE GENERATION  (Hex)"+" "*(w-46)+"║")
    print("╚"+"═"*(w-2)+"╝\n")
    if asm_data is None: print("  ✘  Skipped.\n"); return None
    asm_lines,_=asm_data
    machine=assemble(asm_lines)
    print(f"  {'Hex Bytes (4 bytes/word)':<42}  Instruction")
    print(f"  {'─'*42}  {'─'*22}")
    for line in machine: print(line)
    print(f"\n  ✔  Machine code — {len(machine)} word(s)  (~{len(machine)*4} bytes).\n")
    return machine