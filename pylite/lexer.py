import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List

class TokenType(Enum):
    IDENTIFIER = auto()
    NUMBER     = auto()
    STRING     = auto()
    TRUE       = auto()
    FALSE      = auto()
    IF         = auto()
    ELIF       = auto()
    ELSE       = auto()
    WHILE      = auto()
    DEF        = auto()
    RETURN     = auto()
    CLASS      = auto()
    IMPORT     = auto()
    FROM       = auto()
    AND        = auto()
    OR         = auto()
    NOT        = auto()
    ASSIGN     = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    STAR_ASSIGN = auto()
    SLASH_ASSIGN = auto()
    DOUBLE_SLASH_ASSIGN = auto()
    PERCENT_ASSIGN = auto()
    DOUBLE_STAR_ASSIGN = auto()
    PLUS       = auto()
    MINUS      = auto()
    STAR       = auto()
    SLASH      = auto()
    DOUBLE_SLASH = auto()
    PERCENT    = auto()
    DOUBLE_STAR= auto()
    EQ         = auto()
    NEQ        = auto()
    LT         = auto()
    GT         = auto()
    LPAREN     = auto()
    RPAREN     = auto()
    LBRACKET   = auto()
    RBRACKET   = auto()
    LBRACE     = auto()
    RBRACE     = auto()
    COMMA      = auto()
    COLON      = auto()
    DOT        = auto()
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
        'elif': TokenType.ELIF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'def': TokenType.DEF,
        'return': TokenType.RETURN,
        'class': TokenType.CLASS,
        'import': TokenType.IMPORT,
        'from': TokenType.FROM,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT
    }

    RULES = [
        ('NUMBER',     r'\d+\.\d+|\d+'),
        ('STRING',     r'"[^"]*"|\'[^\']*\''),
        ('DOUBLE_SLASH_ASSIGN', r'//='),
        ('DOUBLE_STAR_ASSIGN',  r'\*\*='),
        ('PLUS_ASSIGN',         r'\+='),
        ('MINUS_ASSIGN',        r'-='),
        ('STAR_ASSIGN',         r'\*='),
        ('SLASH_ASSIGN',        r'/='),
        ('PERCENT_ASSIGN',      r'%='),
        ('DOUBLE_SLASH',        r'//'),
        ('DOUBLE_STAR',         r'\*\*'),
        ('EQ',         r'=='),
        ('NEQ',        r'!='),
        ('ASSIGN',     r'='),
        ('LT',         r'<'),
        ('GT',         r'>'),
        ('IDENTIFIER', r'[a-zA-Z_]\w*'),
        ('PLUS',       r'\+'),
        ('MINUS',      r'-'),
        ('STAR',       r'\*'),
        ('SLASH',      r'/'),
        ('PERCENT',    r'%'),
        ('LPAREN',     r'\('),
        ('RPAREN',     r'\)'),
        ('LBRACKET',   r'\['),
        ('RBRACKET',   r'\]'),
        ('LBRACE',     r'\{'),
        ('RBRACE',     r'\}'),
        ('COMMA',      r','),
        ('COLON',      r':'),
        ('DOT',        r'\.'),
        ('NEWLINE',    r'\r?\n[ \t]*'),
        ('COMMENT',    r'#.*'),
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
                        raise IndentationError(f"Unindent does not match outer level at line {line}")
            else:
                if kind == 'IDENTIFIER' and value in self.KEYWORDS:
                    tokens.append(Token(self.KEYWORDS[value], value, line, column))
                else:
                    tokens.append(Token(TokenType[kind], value, line, column))

        while len(indent_stack) > 1:
            indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, "", line, 0))

        tokens.append(Token(TokenType.EOF, "", line, len(self.source_code) - line_start))
        return tokens