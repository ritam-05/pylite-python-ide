from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.interpreter import Interpreter

def test_interpreter_math():
    lexer = Lexer("2 * 3 + 4")
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    result = interpreter.interpret(ast)
    
    assert result == 10

def test_interpreter_assignment_and_variables():
    code = """
x = 10
y = x * 2 + 5
"""
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    interpreter.interpret(ast)
    
    assert interpreter.environment["x"] == 10
    assert interpreter.environment["y"] == 25

def test_interpreter_undefined_variable():
    lexer = Lexer("y = x + 5")
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    try:
        interpreter.interpret(ast)
        assert False, "Should have raised a NameError"
    except NameError as e:
        assert "name 'x' is not defined" in str(e)

def test_interpreter_print_function(capsys):
    code = """
x = 10
print(x, x * 2)
"""
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    interpreter.interpret(ast)
    
    captured = capsys.readouterr()
    assert captured.out == "10 20\n"

def test_interpreter_comparisons(capsys):
    code = """
x = 10
y = 20
print(x < y)
print(x == 10)
print(x != y)
print(x + 15 > y)
print(False)
"""
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    interpreter.interpret(ast)
    
    captured = capsys.readouterr()
    assert captured.out == "True\nTrue\nTrue\nTrue\nFalse\n"

def test_interpreter_if_statement(capsys):
    code = """
x = 10
if x > 5:
    print(1)
    if x == 10:
        print(2)
if x < 5:
    print(3)
"""
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    interpreter.interpret(ast)
    
    captured = capsys.readouterr()
    assert captured.out == "1\n2\n"

def test_interpreter_while_loop(capsys):
    code = """
x = 3
while x > 0:
    print(x)
    x = x - 1
"""
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    interpreter.interpret(ast)
    
    captured = capsys.readouterr()
    assert captured.out == "3\n2\n1\n"

def test_interpreter_functions_and_recursion(capsys):
    code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    interpreter.interpret(ast)
    
    captured = capsys.readouterr()
    assert captured.out == "120\n"

def test_interpreter_lists(capsys):
    code = """
arr = [10, 20, 30]
print(arr[0])

# Modify the list
arr[1] = 99
print(arr[1])
print(arr[2])
"""
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    interpreter.interpret(ast)
    
    captured = capsys.readouterr()
    assert captured.out == "10\n99\n30\n"