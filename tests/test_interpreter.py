from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.interpreter import Interpreter

def test_interpreter_math():
    lexer = Lexer("2 * 3 + 4")
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    result = interpreter.interpret(ast)
    
    # Precedence dictates 2*3 happens first (6), then + 4 = 10
    assert result == 10

def test_interpreter_assignment_and_variables():
    # A multiline script testing memory
    code = """
x = 10
y = x * 2 + 5
"""
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    interpreter = Interpreter()
    interpreter.interpret(ast)
    
    # Inspect the virtual memory (environment) to see if it worked
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
    
    # Capture the output printed to the console
    captured = capsys.readouterr()
    assert captured.out == "10 20\n"