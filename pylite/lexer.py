import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List

class TokenType(Enum):
    IDENTIFIER = auto()
    NUMBER     = auto()
    TRUE       = auto()  # ADDED
    FALSE      = auto()  # ADDED
    ASSIGN     = auto()
    PLUS       = auto()
    STAR       = auto()
    EQ         = auto()  # ==
    NEQ        = auto()  # !=
    LT         = auto()  # <
    GT         = auto()  # >
    LPAREN     = auto()
    RPAREN     = auto()
    COMMA      = auto()
    NEWLINE    = auto()
    EOF        = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class Lexer:
    # KEYWORDS dictionary to intercept reserved words
    KEYWORDS = {
        'True': TokenType.TRUE,
        'False': TokenType.FALSE
    }

    RULES = [
        ('NUMBER',     r'\d+'),
        ('EQ',         r'=='),  # Must come before ASSIGN (=)
        ('NEQ',        r'!='),
        ('ASSIGN',     r'='),
        ('LT',         r'<'),
        ('GT',         r'>'),
        ('IDENTIFIER', r'[a-zA-Z_]\w*'),
        ('PLUS',       r'\+'),
        ('STAR',       r'\*'),
        ('LPAREN',     r'\('),
        ('RPAREN',     r'\)'),
        ('COMMA',      r','),
        ('NEWLINE',    r'\n'),
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

        for match in self.regex.finditer(self.source_code):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start

            if kind == 'SKIP':
                continue
            elif kind == 'MISMATCH':
                raise SyntaxError(f"Unexpected character '{value}' at line {line}")
            elif kind == 'NEWLINE':
                tokens.append(Token(TokenType.NEWLINE, value, line, column))
                line += 1
                line_start = match.end()
            else:
                # Intercept keywords
                if kind == 'IDENTIFIER' and value in self.KEYWORDS:
                    token_type = self.KEYWORDS[value]
                else:
                    token_type = TokenType[kind]
                
                tokens.append(Token(token_type, value, line, column))

        tokens.append(Token(TokenType.EOF, "", line, len(self.source_code) - line_start))
        return tokens