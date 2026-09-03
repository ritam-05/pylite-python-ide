from typing import List
from pylite.lexer import Token, TokenType
from pylite.ast import *

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        if self.pos < len(self.tokens): return self.tokens[self.pos]
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
                self.eat(TokenType.NEWLINE); continue
            statements.append(self.statement())
        return statements

    def statement(self) -> ASTNode:
        if self.current_token().type == TokenType.CLASS:
            self.eat(TokenType.CLASS)
            name = self.current_token().value
            self.eat(TokenType.IDENTIFIER)

            base = None
            if self.current_token().type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                base = self.current_token().value
                self.eat(TokenType.IDENTIFIER)
                self.eat(TokenType.RPAREN)
                
            self.eat(TokenType.COLON)
            while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE); continue
                body.append(self.statement())
            if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
            return ClassDef(name=name, body=body, base=base)          # Parse the base class (if any)


            self.eat(TokenType.COLON)
            while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE); continue
                body.append(self.statement())
            if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
            return ClassDef(name=name, body=body)
        if self.current_token().type == TokenType.IMPORT:
            self.eat(TokenType.IMPORT)
            module = self.current_token().value
            self.eat(TokenType.IDENTIFIER)
            return Import(module=module)

        if self.current_token().type == TokenType.FROM:
            self.eat(TokenType.FROM)
            module = self.current_token().value
            self.eat(TokenType.IDENTIFIER)
            self.eat(TokenType.IMPORT)
            names = [self.current_token().value]
            self.eat(TokenType.IDENTIFIER)
            while self.current_token().type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                names.append(self.current_token().value)
                self.eat(TokenType.IDENTIFIER)
            return ImportFrom(module=module, names=names)

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
            while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE); continue
                body.append(self.statement())
            if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
            return FunctionDef(name=func_name, params=params, body=body)

        if self.current_token().type == TokenType.RETURN:
            self.eat(TokenType.RETURN)
            return Return(value=self.expression())

        # ADDED: Raise Statement
        if self.current_token().type == TokenType.RAISE:
            self.eat(TokenType.RAISE)
            return Raise(exc=self.expression())

        # ADDED: Try/Except Statements
        if self.current_token().type == TokenType.TRY:
            self.eat(TokenType.TRY)
            self.eat(TokenType.COLON)
            while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE); continue
                body.append(self.statement())
            if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
            
            while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
            
            handlers = []
            while self.current_token().type == TokenType.EXCEPT:
                self.eat(TokenType.EXCEPT)
                exc_type = None
                exc_name = None
                if self.current_token().type != TokenType.COLON:
                    exc_type = self.expression()
                    if self.current_token().type == TokenType.AS:
                        self.eat(TokenType.AS)
                        exc_name = self.current_token().value
                        self.eat(TokenType.IDENTIFIER)
                self.eat(TokenType.COLON)
                
                while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
                self.eat(TokenType.INDENT)
                h_body = []
                while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                    if self.current_token().type == TokenType.NEWLINE:
                        self.eat(TokenType.NEWLINE); continue
                    h_body.append(self.statement())
                if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
                while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
                
                handlers.append(ExceptHandler(type=exc_type, name=exc_name, body=h_body))
                
            return Try(body=body, handlers=handlers)

        if self.current_token().type == TokenType.IF:
            self.eat(TokenType.IF)
            condition = self.expression()
            self.eat(TokenType.COLON)
            
            while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE); continue
                body.append(self.statement())
                
            if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
            while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
                
            orelse = []
            current_orelse_list = orelse
            
            while self.current_token().type == TokenType.ELIF:
                self.eat(TokenType.ELIF)
                elif_cond = self.expression()
                self.eat(TokenType.COLON)
                
                while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
                self.eat(TokenType.INDENT)
                
                elif_body = []
                while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                    if self.current_token().type == TokenType.NEWLINE:
                        self.eat(TokenType.NEWLINE); continue
                    elif_body.append(self.statement())
                    
                if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
                while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
                
                new_if = If(condition=elif_cond, body=elif_body, orelse=[])
                current_orelse_list.append(new_if)
                current_orelse_list = new_if.orelse

            if self.current_token().type == TokenType.ELSE:
                self.eat(TokenType.ELSE)
                self.eat(TokenType.COLON)
                
                while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
                self.eat(TokenType.INDENT)
                
                while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                    if self.current_token().type == TokenType.NEWLINE:
                        self.eat(TokenType.NEWLINE); continue
                    current_orelse_list.append(self.statement())
                    
                if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
                
            return If(condition=condition, body=body, orelse=orelse)

        if self.current_token().type == TokenType.WHILE:
            self.eat(TokenType.WHILE)
            condition = self.expression()
            self.eat(TokenType.COLON)
            while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE); continue
                body.append(self.statement())
            if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
            return While(condition=condition, body=body)

        if self.current_token().type == TokenType.FOR:
            self.eat(TokenType.FOR)
            target = self.expression()
            self.eat(TokenType.IN)
            iter_node = self.expression()
            self.eat(TokenType.COLON)
            
            while self.current_token().type == TokenType.NEWLINE: self.eat(TokenType.NEWLINE)
            self.eat(TokenType.INDENT)
            
            body = []
            while self.current_token().type not in (TokenType.DEDENT, TokenType.EOF):
                if self.current_token().type == TokenType.NEWLINE:
                    self.eat(TokenType.NEWLINE); continue
                body.append(self.statement())
                
            if self.current_token().type == TokenType.DEDENT: self.eat(TokenType.DEDENT)
            return For(target=target, iter=iter_node, body=body)

        expr = self.expression()
        
        assign_tokens = (TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                         TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN, TokenType.DOUBLE_SLASH_ASSIGN,
                         TokenType.PERCENT_ASSIGN, TokenType.DOUBLE_STAR_ASSIGN)
                         
        if self.current_token().type in assign_tokens:
            op_token = self.current_token()
            self.eat(op_token.type)
            value = self.expression()
            if op_token.type == TokenType.ASSIGN: return Assign(target=expr, value=value)
            else: return AugAssign(target=expr, op=op_token.value, value=value)
            
        return Expr(value=expr)

    def expression(self) -> ASTNode:
        return self.logic_or()

    def logic_or(self) -> ASTNode:
        node = self.logic_and()
        while self.current_token().type == TokenType.OR:
            op = self.current_token().value
            self.eat(TokenType.OR)
            node = LogicalOp(left=node, op=op, right=self.logic_and())
        return node

    def logic_and(self) -> ASTNode:
        node = self.logic_not()
        while self.current_token().type == TokenType.AND:
            op = self.current_token().value
            self.eat(TokenType.AND)
            node = LogicalOp(left=node, op=op, right=self.logic_not())
        return node

    def logic_not(self) -> ASTNode:
        if self.current_token().type == TokenType.NOT:
            op = self.current_token().value
            self.eat(TokenType.NOT)
            return UnaryOp(op=op, operand=self.logic_not())
        return self.comparison()

    def comparison(self) -> ASTNode:
        node = self.expr()
        while self.current_token().type in (TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT):
            op = self.current_token().value
            self.eat(self.current_token().type)
            node = BinOp(left=node, op=op, right=self.expr())
        return node

    def expr(self) -> ASTNode:
        node = self.term()
        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token().value
            self.eat(self.current_token().type)
            node = BinOp(left=node, op=op, right=self.term())
        return node

    def term(self) -> ASTNode:
        node = self.unary()
        while self.current_token().type in (TokenType.STAR, TokenType.SLASH, TokenType.DOUBLE_SLASH, TokenType.PERCENT):
            op = self.current_token().value
            self.eat(self.current_token().type)
            node = BinOp(left=node, op=op, right=self.unary())
        return node

    def unary(self) -> ASTNode:
        if self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token().value
            self.eat(self.current_token().type)
            return UnaryOp(op=op, operand=self.unary())
        return self.power()

    def power(self) -> ASTNode:
        node = self.factor()
        if self.current_token().type == TokenType.DOUBLE_STAR:
            op = self.current_token().value
            self.eat(TokenType.DOUBLE_STAR)
            node = BinOp(left=node, op=op, right=self.unary()) 
        return node

    def factor(self) -> ASTNode:
        token = self.current_token()
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            val = float(token.value) if '.' in token.value else int(token.value)
            node = Number(value=val)
        elif token.type == TokenType.STRING:
            self.eat(TokenType.STRING)
            node = String(value=token.value[1:-1])
        elif token.type == TokenType.TRUE:
            self.eat(TokenType.TRUE)
            node = Boolean(value=True)
        elif token.type == TokenType.FALSE:
            self.eat(TokenType.FALSE)
            node = Boolean(value=False)
        elif token.type == TokenType.SUPER:
            self.eat(TokenType.SUPER)
            self.eat(TokenType.LPAREN)
            self.eat(TokenType.RPAREN)
            node = Super()
        elif token.type == TokenType.IDENTIFIER:
            self.eat(TokenType.IDENTIFIER)
            node = Name(value=token.value)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expression()
            self.eat(TokenType.RPAREN)
        elif token.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            
            lower = None
            upper = None
            step = None
            is_slice = False
            
            if self.current_token().type != TokenType.COLON and self.current_token().type != TokenType.RBRACKET:
                lower = self.expression()
                
            if self.current_token().type == TokenType.COLON:
                is_slice = True
                self.eat(TokenType.COLON)
                if self.current_token().type not in (TokenType.RBRACKET, TokenType.COLON):
                    upper = self.expression()
                if self.current_token().type == TokenType.COLON:
                    self.eat(TokenType.COLON)
                    if self.current_token().type != TokenType.RBRACKET:
                        step = self.expression()
            
            self.eat(TokenType.RBRACKET)
            
            if is_slice:
                node = Subscript(obj=node, index=Slice(lower=lower, upper=upper, step=step))
            else:
                if lower is None:
                    elements = []
                else:
                    elements = [lower]
                    while self.current_token().type == TokenType.COMMA:
                        self.eat(TokenType.COMMA)
                        elements.append(self.expression())
                node = ListLiteral(elements=elements)
            
        elif token.type == TokenType.LBRACE:
            self.eat(TokenType.LBRACE)
            keys = []; values = []
            if self.current_token().type != TokenType.RBRACE:
                keys.append(self.expression())
                self.eat(TokenType.COLON)
                values.append(self.expression())
                while self.current_token().type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    keys.append(self.expression())
                    self.eat(TokenType.COLON)
                    values.append(self.expression())
            self.eat(TokenType.RBRACE)
            node = DictLiteral(keys=keys, values=values)
        else:
            raise SyntaxError(f"Unexpected token: {token.type.name} at line {token.line}")

        while self.current_token().type in (TokenType.LPAREN, TokenType.LBRACKET, TokenType.DOT):
            if self.current_token().type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                args = []
                if self.current_token().type != TokenType.RPAREN:
                    args.append(self.expression())
                    while self.current_token().type == TokenType.COMMA:
                        self.eat(TokenType.COMMA)
                        args.append(self.expression())
                self.eat(TokenType.RPAREN)
                node = Call(func=node, args=args)
                
            elif self.current_token().type == TokenType.LBRACKET:
                self.eat(TokenType.LBRACKET)
                
                lower = None
                upper = None
                step = None
                is_slice = False
                
                if self.current_token().type != TokenType.COLON:
                    lower = self.expression()
                    
                if self.current_token().type == TokenType.COLON:
                    is_slice = True
                    self.eat(TokenType.COLON)
                    if self.current_token().type not in (TokenType.RBRACKET, TokenType.COLON):
                        upper = self.expression()
                    if self.current_token().type == TokenType.COLON:
                        self.eat(TokenType.COLON)
                        if self.current_token().type != TokenType.RBRACKET:
                            step = self.expression()
                
                self.eat(TokenType.RBRACKET)
                
                if is_slice:
                    node = Subscript(obj=node, index=Slice(lower=lower, upper=upper, step=step))
                else:
                    node = Subscript(obj=node, index=lower)
                
            elif self.current_token().type == TokenType.DOT:
                self.eat(TokenType.DOT)
                attr_name = self.current_token().value
                self.eat(TokenType.IDENTIFIER)
                node = Attribute(obj=node, attr=attr_name)
                
        return node