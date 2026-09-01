from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.compiler import Compiler
from pylite.vm import VM

def execute_vm(code: str):
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    compiler = Compiler()
    main_func = compiler.compile(ast)
    
    vm = VM()
    return vm.run(main_func)

def test_vm_math():
    result = execute_vm("x = 10 * 2 + 5\nreturn x")
    assert result == 25

def test_vm_if_statement(capsys):
    code = """
x = 10
if x > 5:
    print(1)
"""
    execute_vm(code)
    captured = capsys.readouterr()
    assert captured.out == "1\n"

def test_vm_while_loop(capsys):
    code = """
x = 3
while x > 0:
    print(x)
    x = x - 1
"""
    execute_vm(code)
    captured = capsys.readouterr()
    assert captured.out == "3\n2\n1\n"

def test_vm_recursion(capsys):
    code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""
    execute_vm(code)
    captured = capsys.readouterr()
    assert captured.out == "120\n"