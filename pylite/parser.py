from typing import List
from pylite.lexer import Token, TokenType
from pylite.ast import ASTNode, Number, Boolean, Name, BinOp, Assign, Call, If

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def eat(self, token_type: TokenType):
        if self.current_token().type == token_type:
            self.pos += 1
        else:
            raise SyntaxError(f"Expected {token_type.name}, got {self.current_token().type.name} at line {self.current_token().line}")

    def parse(self) -> List[ASTNode]:
        statements = []
        while self.current_token().type != TokenType.EOF:
            if self.current_token().type == TokenType.NEWLINE:
                self.eat(TokenType.NEWLINE)
                continue
            statements.append(self.statement())
        return statements

    def statement(self) -> ASTNode:
        # ADDED: Parse IF statements
        if self.current_token().type == TokenType.IF:
            self.eat(TokenType.IF)
            condition = self.comparison()
            self.eat(TokenType.COLON)
            
            # Consume newlines immediately following the colon
            while self.current_token().type == TokenType.NEWLINE:
                self.eat(TokenType.NEWLINE)
                
            self.eat(TokenType.INDENT)
            
            body = []
            # Keep parsing statements until we hit a DEDENT or end of file
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE)
                    continue
                body.append(self.statement())
                
            if self.current_token().type == TokenType.DEDENT:
                self.eat(TokenType.DEDENT)
                
            return If(condition=condition, body=body)

        if self.current_token().type == TokenType.IDENTIFIER:
            next_pos = self.pos + 1
            if next_pos < len(self.tokens) and self.tokens[next_pos].type == TokenType.ASSIGN:
                name = self.current_token().value
                self.eat(TokenType.IDENTIFIER)
                self.eat(TokenType.ASSIGN)
                value = self.comparison()
                return Assign(name=name, value=value)
        
        return self.comparison()

    def comparison(self) -> ASTNode:
        node = self.expr()
        while self.current_token().type in (TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT):
            op_token = self.current_token()
            self.eat(op_token.type)
            node = BinOp(left=node, op=op_token.value, right=self.expr())
        return node

    def expr(self) -> ASTNode:
        node = self.term()
        while self.current_token().type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            node = BinOp(left=node, op='+', right=self.term())
        return node

    def term(self) -> ASTNode:
        node = self.factor()
        while self.current_token().type == TokenType.STAR:
            self.eat(TokenType.STAR)
            node = BinOp(left=node, op='*', right=self.factor())
        return node

    def factor(self) -> ASTNode:
        token = self.current_token()
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(value=int(token.value))
        elif token.type == TokenType.TRUE:
            self.eat(TokenType.TRUE)
            return Boolean(value=True)
        elif token.type == TokenType.FALSE:
            self.eat(TokenType.FALSE)
            return Boolean(value=False)
        elif token.type == TokenType.IDENTIFIER:
            self.eat(TokenType.IDENTIFIER)
            name_node = Name(value=token.value)
            if self.current_token().type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                args = []
                if self.current_token().type != TokenType.RPAREN:
                    args.append(self.comparison())
                    while self.current_token().type == TokenType.COMMA:
                        self.eat(TokenType.COMMA)
                        args.append(self.comparison())
                self.eat(TokenType.RPAREN)
                return Call(func=name_node, args=args)
            return name_node
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.comparison()
            self.eat(TokenType.RPAREN)
            return node
        else:
            raise SyntaxError(f"Unexpected token: {token.type.name} at line {token.line}")