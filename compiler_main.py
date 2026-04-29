"""
╔══════════════════════════════════════════════════════════════╗
║   ConciseLang Mini-Compiler  v5.0  —  All 7 Phases          ║
║   Phase 2 : Syntax Tree   (box-drawing ASCII tree)          ║
║   Phase 3 : Annotated Semantic Tree + Symbol Table          ║
║   Usage:                                                     ║
║     python compiler_main.py                  interactive     ║
║     python compiler_main.py program.cl       from file       ║
║     cat prog.cl | python compiler_main.py    from stdin      ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, os

_HERE   = os.path.dirname(os.path.abspath(__file__))
_PHASES = os.path.join(_HERE, "phases")
sys.path.insert(0, _PHASES if os.path.isdir(_PHASES) else _HERE)

from phase1_lexer       import run_lexer
from phase2_parser      import run_parser
from phase3_semantic    import run_semantic
from phase4_irgen       import run_irgen
from phase5_optimizer   import run_optimizer
from phase6_codegen     import run_codegen
from phase7_machinecode import run_machinecode

DEMO = """\
# ConciseLang v5 – Full Demo
let name   = "Alice"
let score  = 95.5
let age    = 20
let pi     = 3.14
let x, y   = 6, 7
let active = yes
let status = if (score > 50) "Pass" else "Fail"
let mood   = if (age > 18) "Adult" else "Minor"
func add(a, b) { a + b }
fn square(n)   { n * n }
fn double(n)   { n + n }
score  |> print
status |> print
x, y   |> add    |> print
x      |> square |> double |> print
for 0..5 as i {
    i |> print
}
let counter = 3
while (counter > 0) {
    counter |> print
}
let nums = [1, 2, 3, 4, 5]
from nums where n > 2 select n * n
let area = pi * square(4)
area |> print
"""

SYNTAX_CARD = """
┌──────────────────────────────────────────────────────────┐
│  ConciseLang v5  –  Quick Reference                      │
├──────────────────────────────────────────────────────────┤
│  let x = 42                   type inference             │
│  let a, b = 10, 20            multi-assign               │
│  let s = if (x>0) "y" else "n"  expression-if           │
│  func add(a,b) { a + b }      implicit-return func       │
│  fn square(n)  { n * n }      fn shorthand               │
│  for 0..5 as i { i |> print } range loop                 │
│  while (x > 0) { x |> print } while loop                │
│  from list where n>2 select n*n  SQL-style query         │
│  x         |> print           pipe  (= print(x))         │
│  a, b      |> add |> print    multi-arg pipe             │
│  x |> sq   |> double |> print pipe chain                 │
│  let flag = yes / no          boolean literals           │
│  # comment                                               │
└──────────────────────────────────────────────────────────┘
Commands:  END = compile    SHOW = load demo    QUIT = exit
"""

def _halt(phase: int, name: str):
    print()
    print("  " + "✘"*32)
    print(f"  Pipeline HALTED at Phase {phase} — {name}")
    print(f"  Fix the error(s) above and recompile.")
    print("  " + "✘"*32 + "\n")

def run_pipeline(source: str, label: str = ""):
    print()
    print("█"*62)
    print(f"  SOURCE PROGRAM  [{label}]" if label else "  SOURCE PROGRAM")
    print("█"*62)
    for ln, line in enumerate(source.splitlines(), 1):
        print(f"  {ln:3d} │ {line}")
    print()

    print(); tokens = run_lexer(source)
    if not tokens:          _halt(1,"Lexical Analysis");   return
    print(); ast = run_parser(tokens)
    if not ast:             _halt(2,"Syntax Analysis");    return
    print(); ast, analyzer = run_semantic(ast)
    if not ast:             _halt(3,"Semantic Analysis");  return
    print(); ir = run_irgen(ast)
    if not ir:              _halt(4,"IR Generation");      return
    print(); ir_opt = run_optimizer(ir)
    if not ir_opt:          _halt(5,"Optimization");       return
    print(); asm = run_codegen(ir_opt)
    if not asm:             _halt(6,"Code Generation");    return
    print(); mc = run_machinecode(asm)

    vis = [t for t in tokens if t.type not in ("NEWLINE","EOF")]
    print("█"*62)
    print("  ✔  ALL 7 PHASES COMPLETED SUCCESSFULLY")
    print("█"*62)
    print(f"""
  ┌─────────────────────────────────────────┐
  │  Tokens produced   :  {len(vis):<6}              │
  │  IR instructions   :  {len(ir):<6}              │
  │  Optimised IR      :  {len(ir_opt):<6}              │
  │  Assembly lines    :  {len(asm[0]):<6}              │
  │  Machine words     :  {len(mc) if mc else 0:<6}              │
  │  Estimated bytes   :  {len(mc)*4 if mc else 0:<6}              │
  └─────────────────────────────────────────┘
""")

def get_source():
    if len(sys.argv) == 2:
        path = sys.argv[1]
        if not os.path.exists(path):
            print(f"  ✘  File not found: {path}"); sys.exit(1)
        with open(path, encoding="utf-8") as f:
            return f.read(), os.path.basename(path)
    if not sys.stdin.isatty():
        return sys.stdin.read(), "stdin"
    print(SYNTAX_CARD)
    lines = []
    while True:
        try:
            line = input("  ❯ ")
        except (EOFError, KeyboardInterrupt):
            print(); break
        cmd = line.strip().upper()
        if cmd == "END":   break
        if cmd == "QUIT":  sys.exit(0)
        if cmd == "SHOW":  return DEMO, "demo"
        lines.append(line)
    return "\n".join(lines), "interactive"

if __name__ == "__main__":
    src, label = get_source()
    if src.strip():
        run_pipeline(src, label)
    else:
        print("  ✘  No source provided. Type SHOW for the built-in demo.")