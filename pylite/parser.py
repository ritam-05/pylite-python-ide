from typing import List
from pylite.lexer import Token, TokenType
from pylite.ast import ASTNode, Number, Boolean, Name, BinOp, Assign, Call, If, While, FunctionDef, Return, ListLiteral, Subscript

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
        if self.current_token().type == TokenType.DEF:
            self.eat(TokenType.DEF)
            func_name = self.current_token().value
            self.eat(TokenType.IDENTIFIER)
            self.eat(TokenType.LPAREN)
            params = []
            if self.current_token().type != TokenType.RPAREN:
                params.append(self.current_token().value)
                self.eat(TokenType.IDENTIFIER)
                while self.current_token().type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    params.append(self.current_token().value)
                    self.eat(TokenType.IDENTIFIER)
            self.eat(TokenType.RPAREN)
            self.eat(TokenType.COLON)
            while self.current_token().type == TokenType.NEWLINE:
                self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE)
                    continue
                body.append(self.statement())
            if self.current_token().type == TokenType.DEDENT:
                self.eat(TokenType.DEDENT)
            return FunctionDef(name=func_name, params=params, body=body)

        if self.current_token().type == TokenType.RETURN:
            self.eat(TokenType.RETURN)
            value = self.comparison()
            return Return(value=value)

        if self.current_token().type == TokenType.IF:
            self.eat(TokenType.IF)
            condition = self.comparison()
            self.eat(TokenType.COLON)
            while self.current_token().type == TokenType.NEWLINE:
                self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE)
                    continue
                body.append(self.statement())
            if self.current_token().type == TokenType.DEDENT:
                self.eat(TokenType.DEDENT)
            return If(condition=condition, body=body)

        if self.current_token().type == TokenType.WHILE:
            self.eat(TokenType.WHILE)
            condition = self.comparison()
            self.eat(TokenType.COLON)
            while self.current_token().type == TokenType.NEWLINE:
                self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE)
                    continue
                body.append(self.statement())
            if self.current_token().type == TokenType.DEDENT:
                self.eat(TokenType.DEDENT)
            return While(condition=condition, body=body)

        # MODIFIED: A much cleaner way to handle assignments!
        # First, parse an expression.
        expr = self.comparison()
        
        # If the very next token is an '=', it means this was an assignment.
        if self.current_token().type == TokenType.ASSIGN:
            self.eat(TokenType.ASSIGN)
            value = self.comparison()
            return Assign(target=expr, value=value)
            
        return expr

    def comparison(self) -> ASTNode:
        node = self.expr()
        while self.current_token().type in (TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT):
            op_token = self.current_token()
            self.eat(op_token.type)
            node = BinOp(left=node, op=op_token.value, right=self.expr())
        return node

    def expr(self) -> ASTNode:
        node = self.term()
        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.current_token()
            self.eat(op_token.type)
            node = BinOp(left=node, op=op_token.value, right=self.term())
        return node

    def term(self) -> ASTNode:
        node = self.factor()
        while self.current_token().type == TokenType.STAR:
            self.eat(TokenType.STAR)
            node = BinOp(left=node, op='*', right=self.factor())
        return node

    def factor(self) -> ASTNode:
        token = self.current_token()
        
        # 1. Parse the base value
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            node = Number(value=int(token.value))
        elif token.type == TokenType.TRUE:
            self.eat(TokenType.TRUE)
            node = Boolean(value=True)
        elif token.type == TokenType.FALSE:
            self.eat(TokenType.FALSE)
            node = Boolean(value=False)
        elif token.type == TokenType.IDENTIFIER:
            self.eat(TokenType.IDENTIFIER)
            node = Name(value=token.value)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.comparison()
            self.eat(TokenType.RPAREN)
        elif token.type == TokenType.LBRACKET: # ADDED: Parse Lists
            self.eat(TokenType.LBRACKET)
            elements = []
            if self.current_token().type != TokenType.RBRACKET:
                elements.append(self.comparison())
                while self.current_token().type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    elements.append(self.comparison())
            self.eat(TokenType.RBRACKET)
            node = ListLiteral(elements=elements)
        else:
            raise SyntaxError(f"Unexpected token: {token.type.name} at line {token.line}")

        # 2. Check for postfix operators (Function calls or List Indexing)
        # This loops, allowing chained operations like `matrix[0][1]()`
        while self.current_token().type in (TokenType.LPAREN, TokenType.LBRACKET):
            if self.current_token().type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                args = []
                if self.current_token().type != TokenType.RPAREN:
                    args.append(self.comparison())
                    while self.current_token().type == TokenType.COMMA:
                        self.eat(TokenType.COMMA)
                        args.append(self.comparison())
                self.eat(TokenType.RPAREN)
                node = Call(func=node, args=args)
                
            elif self.current_token().type == TokenType.LBRACKET:
                self.eat(TokenType.LBRACKET)
                index = self.comparison()
                self.eat(TokenType.RBRACKET)
                node = Subscript(obj=node, index=index)
                
        return node