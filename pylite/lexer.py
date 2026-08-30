import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List

class TokenType(Enum):
    IDENTIFIER = auto()
    NUMBER     = auto()
    ASSIGN     = auto()
    PLUS       = auto()
    LPAREN     = auto()
    RPAREN     = auto()
    NEWLINE    = auto()
    EOF        = auto()  # End of File

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, line={self.line}, col={self.column})"

class Lexer:
    # Define regex patterns for each token type
    # Order matters! We use named capture groups: (?P<NAME>pattern)
    RULES = [
        ('NUMBER',     r'\d+'),
        ('IDENTIFIER', r'[a-zA-Z_]\w*'),
        ('ASSIGN',     r'='),
        ('PLUS',       r'\+'),
        ('LPAREN',     r'\('),
        ('RPAREN',     r'\)'),
        ('NEWLINE',    r'\n'),
        ('SKIP',       r'[ \t]+'),   # Spaces and tabs (we will ignore these)
        ('MISMATCH',   r'.'),        # Any other character (will cause an error)
    ]

    def __init__(self, source_code: str):
        self.source_code = source_code
        # Combine all rules into one massive regular expression
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
                raise SyntaxError(f"Unexpected character '{value}' at line {line}, column {column}")
            elif kind == 'NEWLINE':
                # We record the newline token, then update our line and column counters
                tokens.append(Token(TokenType.NEWLINE, value, line, column))
                line += 1
                line_start = match.end()
            else:
                # Convert the string name back to the Enum
                token_type = TokenType[kind]
                tokens.append(Token(token_type, value, line, column))

        # Always append an EOF token so the parser knows when to stop
        tokens.append(Token(TokenType.EOF, "", line, len(self.source_code) - line_start))
        return tokens