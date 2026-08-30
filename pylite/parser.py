from typing import List
from pylite.lexer import Token, TokenType
from pylite.ast import ASTNode, Number, Name, BinOp, Assign

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def eat(self, token_type: TokenType):
        """Consume the current token if it matches the expected type, otherwise error."""
        if self.current_token().type == token_type:
            self.pos += 1
        else:
            raise SyntaxError(
                f"Expected {token_type.name}, got {self.current_token().type.name} "
                f"at line {self.current_token().line}"
            )

    def parse(self) -> List[ASTNode]:
        """Parse the entire token list into a list of statements."""
        statements = []
        while self.current_token().type != TokenType.EOF:
            if self.current_token().type == TokenType.NEWLINE:
                self.eat(TokenType.NEWLINE)
                continue
            statements.append(self.statement())
        return statements

    def statement(self) -> ASTNode:
        """statement -> assignment | expr"""
        # Lookahead: if we see IDENTIFIER followed by ASSIGN, it's an assignment
        if self.current_token().type == TokenType.IDENTIFIER:
            next_pos = self.pos + 1
            if next_pos < len(self.tokens) and self.tokens[next_pos].type == TokenType.ASSIGN:
                name = self.current_token().value
                self.eat(TokenType.IDENTIFIER)
                self.eat(TokenType.ASSIGN)
                value = self.expr()
                return Assign(name=name, value=value)
        
        # Otherwise, treat it as an expression
        return self.expr()

    def expr(self) -> ASTNode:
        """expr -> term (PLUS term)*"""
        node = self.term()
        while self.current_token().type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            node = BinOp(left=node, op='+', right=self.term())
        return node

    def term(self) -> ASTNode:
        """term -> factor (STAR factor)*"""
        node = self.factor()
        while self.current_token().type == TokenType.STAR:
            self.eat(TokenType.STAR)
            node = BinOp(left=node, op='*', right=self.factor())
        return node

    def factor(self) -> ASTNode:
        """factor -> NUMBER | IDENTIFIER | LPAREN expr RPAREN"""
        token = self.current_token()
        
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(value=int(token.value))
        
        elif token.type == TokenType.IDENTIFIER:
            self.eat(TokenType.IDENTIFIER)
            return Name(value=token.value)
        
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
            
        else:
            raise SyntaxError(f"Unexpected token in expression: {token.type.name} ('{token.value}')")