from pylite.lexer import Lexer, TokenType

def test_tokenize_assignment():
    lexer = Lexer("x = 10")
    tokens = lexer.tokenize()
    
    assert len(tokens) == 4 # IDENTIFIER, ASSIGN, NUMBER, EOF
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].value == "x"
    assert tokens[1].type == TokenType.ASSIGN
    assert tokens[2].type == TokenType.NUMBER
    assert tokens[2].value == "10"
    assert tokens[3].type == TokenType.EOF

def test_tokenize_multiline_program():
    code = """x = 10
y = 20
print(x + y)"""
    
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    
    # We expect 14 tokens in total, including NEWLINEs and EOF
    types = [t.type for t in tokens]
    expected_types = [
        TokenType.IDENTIFIER, TokenType.ASSIGN, TokenType.NUMBER, TokenType.NEWLINE,
        TokenType.IDENTIFIER, TokenType.ASSIGN, TokenType.NUMBER, TokenType.NEWLINE,
        TokenType.IDENTIFIER, TokenType.LPAREN, TokenType.IDENTIFIER, TokenType.PLUS,
        TokenType.IDENTIFIER, TokenType.RPAREN, TokenType.EOF
    ]
    
    assert types == expected_types

def test_lexer_error():
    lexer = Lexer("x = @")
    try:
        lexer.tokenize()
        assert False, "Should have raised a SyntaxError for invalid character"
    except SyntaxError as e:
        assert "Unexpected character '@'" in str(e)