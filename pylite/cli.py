import sys
import os
import re
from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.compiler import Compiler
from pylite.vm import VM
from pylite.gui import PyLiteIDE

def run_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
            
        lexer = Lexer(code)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        
        compiler = Compiler()
        main_func = compiler.compile(ast)
        
        vm = VM() # Automatically defaults to sys.stdin input()
        vm.run(main_func)
        
    except Exception as e:
        err_type = type(e).__name__
        err_msg = str(e)
        
        line_match = re.search(r'at line (\d+)', err_msg)
        line_str = f"Line: {line_match.group(1)}\n" if line_match else ""
        
        filename = os.path.basename(filepath)
        
        print(f"\nPyLite {err_type}")
        print(f"File: {filename}")
        if line_str: print(line_str.strip())
        print(f"\n{err_type}: {err_msg}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("Usage:")
        print("  python -m pylite.cli <file.py>  # Run a file directly")
        print("  python -m pylite.cli --gui      # Launch the IDE")
        sys.exit(0)
        
    if sys.argv[1] == "--gui":
        ide = PyLiteIDE()
        ide.run()
    else:
        run_file(sys.argv[1])

if __name__ == "__main__":
    main()