**How to use this Compiler**
1. python compiler_main.py test1_full.cl              # all 7 phases pass
2. python compiler_main.py test2_pipe.cl     # all 7 phases pass
3. python compiler_main.py test3_sql_list.cl         # all 7 phases pass
4. python compiler_main.py test4_semantic_error.cl   # halts at Phase 3
5. python compiler_main.py test5_lexer_error.cl      # halts at Phase 1
6. python compiler_main.py                            # interactive (type SHOW)