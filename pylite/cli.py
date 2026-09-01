import argparse
import sys
from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.compiler import Compiler
from pylite.vm import VM

def execute_code(source_code: str):
    try:
        lexer = Lexer(source_code)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        
        compiler = Compiler()
        main_func = compiler.compile(ast)
        
        vm = VM()
        vm.run(main_func)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="PyLite Compiler and Runtime")
    parser.add_argument("file", nargs="?", help="The .py file to execute")
    parser.add_argument("--gui", action="store_true", help="Launch the Desktop IDE")
    
    args = parser.parse_args()
    
    if args.gui:
        # We will build this file next!
        from pylite.gui import PyLiteIDE
        app = PyLiteIDE()
        app.run()
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                content = f.read()
            execute_code(content)
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()