import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List

class TokenType(Enum):
    IDENTIFIER = auto()
    NUMBER     = auto()
    TRUE       = auto()
    FALSE      = auto()
    IF         = auto()
    WHILE      = auto()
    DEF        = auto()
    RETURN     = auto()
    ASSIGN     = auto()
    PLUS       = auto()
    MINUS      = auto()
    STAR       = auto()
    EQ         = auto()
    NEQ        = auto()
    LT         = auto()
    GT         = auto()
    LPAREN     = auto()
    RPAREN     = auto()
    LBRACKET   = auto()
    RBRACKET   = auto()
    COMMA      = auto()
    COLON      = auto()
    NEWLINE    = auto()
    INDENT     = auto()
    DEDENT     = auto()
    EOF        = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class Lexer:
    KEYWORDS = {
        'True': TokenType.TRUE,
        'False': TokenType.FALSE,
        'if': TokenType.IF,
        'while': TokenType.WHILE,
        'def': TokenType.DEF,
        'return': TokenType.RETURN
    }

    RULES = [
        ('NUMBER',     r'\d+'),
        ('EQ',         r'=='),
        ('NEQ',        r'!='),
        ('ASSIGN',     r'='),
        ('LT',         r'<'),
        ('GT',         r'>'),
        ('IDENTIFIER', r'[a-zA-Z_]\w*'),
        ('PLUS',       r'\+'),
        ('MINUS',      r'-'),
        ('STAR',       r'\*'),
        ('LPAREN',     r'\('),
        ('RPAREN',     r'\)'),
        ('LBRACKET',   r'\['),
        ('RBRACKET',   r'\]'),
        ('COMMA',      r','),
        ('COLON',      r':'),
        ('NEWLINE',    r'\r?\n[ \t]*'),
        ('COMMENT',    r'#.*'),         # ADDED: Match '#' followed by any characters
        ('SKIP',       r'[ \t]+'),
        ('MISMATCH',   r'.'),
    ]

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.regex = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.RULES))

    def tokenize(self) -> List[Token]:
        tokens = []
        line = 1
        line_start = 0
        indent_stack = [0]

        for match in self.regex.finditer(self.source_code):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start

            # MODIFIED: Ignore both SKIP and COMMENT tokens
            if kind in ('SKIP', 'COMMENT'):
                continue
            elif kind == 'MISMATCH':
                raise SyntaxError(f"Unexpected character '{value}' at line {line}")
            
            elif kind == 'NEWLINE':
                spaces = value.replace('\r', '').replace('\n', '')
                indent_level = len(spaces)

                tokens.append(Token(TokenType.NEWLINE, "\n", line, column))
                line += 1
                line_start = match.end() - indent_level

                if indent_level > indent_stack[-1]:
                    indent_stack.append(indent_level)
                    tokens.append(Token(TokenType.INDENT, spaces, line, 0))
                elif indent_level < indent_stack[-1]:
                    while indent_level < indent_stack[-1]:
                        indent_stack.pop()
                        tokens.append(Token(TokenType.DEDENT, "", line, 0))
                    if indent_level != indent_stack[-1]:
                        raise IndentationError(f"Unindent does not match any outer indentation level at line {line}")
            else:
                if kind == 'IDENTIFIER' and value in self.KEYWORDS:
                    token_type = self.KEYWORDS[value]
                else:
                    token_type = TokenType[kind]
                tokens.append(Token(token_type, value, line, column))

        while len(indent_stack) > 1:
            indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, "", line, 0))

        tokens.append(Token(TokenType.EOF, "", line, len(self.source_code) - line_start))
        return tokens