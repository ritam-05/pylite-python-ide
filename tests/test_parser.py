from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.ast import Number, Name, BinOp, Assign

def test_parse_assignment():
    lexer = Lexer("x = 10")
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    assert len(ast) == 1
    assert isinstance(ast[0], Assign)
    assert ast[0].name == "x"
    assert isinstance(ast[0].value, Number)
    assert ast[0].value.value == 10

def test_operator_precedence():
    # Because * has higher precedence, 2 * 3 should be grouped together inside the BinOp
    lexer = Lexer("x + 2 * 3")
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    expr = ast[0]
    assert isinstance(expr, BinOp)
    assert expr.op == '+'
    assert isinstance(expr.left, Name)
    assert expr.left.value == "x"
    
    # The right side of the + should be the multiplication (2 * 3)
    assert isinstance(expr.right, BinOp)
    assert expr.right.op == '*'
    assert expr.right.left.value == 2
    assert expr.right.right.value == 3

def test_parentheses():
    # Parentheses override precedence
    lexer = Lexer("(x + 2) * 3")
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    expr = ast[0]
    assert isinstance(expr, BinOp)
    assert expr.op == '*'
    
    # The left side should now be the addition
    assert isinstance(expr.left, BinOp)
    assert expr.left.op == '+'
    assert expr.left.left.value == "x"
    assert expr.left.right.value == 2