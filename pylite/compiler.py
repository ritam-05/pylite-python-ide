from typing import List, Any
from pylite.ast import *
from pylite.bytecode import Op, Instruction, PyLiteFunction

class Compiler:
    def __init__(self):
        self.instructions: List[Instruction] = []

    def emit(self, opcode: Op, arg: Any = None):
        self.instructions.append(Instruction(opcode, arg))
        return len(self.instructions) - 1

    def compile(self, statements: List[ASTNode]) -> PyLiteFunction:
        self.instructions = []
        for stmt in statements:
            self.visit(stmt)
        self.emit(Op.LOAD_CONST, None)
        self.emit(Op.RETURN_VALUE)
        return PyLiteFunction("<main>", [], self.instructions)

    def _emit_binop(self, op: str):
        if op == '+': self.emit(Op.ADD)
        elif op == '-': self.emit(Op.SUB)
        elif op == '*': self.emit(Op.MUL)
        elif op == '/': self.emit(Op.DIV)
        elif op == '//': self.emit(Op.FLOORDIV)
        elif op == '%': self.emit(Op.MOD)
        elif op == '**': self.emit(Op.POW)
        else: raise NotImplementedError(f"Unknown binop {op}")

    def visit(self, node: ASTNode):
        if isinstance(node, Number): self.emit(Op.LOAD_CONST, node.value)
        elif isinstance(node, Boolean): self.emit(Op.LOAD_CONST, node.value)
        elif isinstance(node, String): self.emit(Op.LOAD_CONST, node.value)
        elif isinstance(node, Name): self.emit(Op.LOAD_NAME, node.value)
        elif isinstance(node, BinOp): self.visit_BinOp(node)
        elif isinstance(node, LogicalOp): self.visit_LogicalOp(node)
        elif isinstance(node, UnaryOp): self.visit_UnaryOp(node)
        elif isinstance(node, Expr): self.visit_Expr(node)
        elif isinstance(node, Assign): self.visit_Assign(node)
        elif isinstance(node, AugAssign): self.visit_AugAssign(node) 
        elif isinstance(node, If): self.visit_If(node)
        elif isinstance(node, While): self.visit_While(node)
        elif isinstance(node, For): self.visit_For(node)
        elif isinstance(node, Try): self.visit_Try(node)
        elif isinstance(node, Raise): self.visit_Raise(node)
        elif isinstance(node, FunctionDef): self.visit_FunctionDef(node)
        elif isinstance(node, Call): self.visit_Call(node)
        elif isinstance(node, Return): self.visit_Return(node)
        elif isinstance(node, ListLiteral): self.visit_ListLiteral(node)
        elif isinstance(node, TupleLiteral): self.visit_TupleLiteral(node) # ADDED
        elif isinstance(node, DictLiteral): self.visit_DictLiteral(node)
        elif isinstance(node, Subscript): self.visit_Subscript(node)
        elif isinstance(node, Slice): self.visit_Slice(node)
        elif isinstance(node, ClassDef): self.visit_ClassDef(node)
        elif isinstance(node, Super): self.visit_Super(node)
        elif isinstance(node, Attribute): self.visit_Attribute(node)
        elif isinstance(node, Import): self.visit_Import(node)
        elif isinstance(node, ImportFrom): self.visit_ImportFrom(node)
        else: raise NotImplementedError(f"Compiler missing: {type(node).__name__}")

    def visit_Raise(self, node: Raise):
        self.visit(node.exc)
        self.emit(Op.RAISE_EXC)
        
    def visit_Try(self, node: Try):
        catch_idx = self.emit(Op.SETUP_CATCH)
        for stmt in node.body: self.visit(stmt)
        self.emit(Op.POP_CATCH)
        jump_end_idx = self.emit(Op.JUMP)
        
        self.instructions[catch_idx].arg = len(self.instructions)
        end_jumps = [jump_end_idx]
        
        for handler in node.handlers:
            if handler.type is not None:
                self.emit(Op.DUP_TOP)
                self.visit(handler.type)
                self.emit(Op.CHECK_EXC_MATCH)
                jump_next_idx = self.emit(Op.JUMP_IF_FALSE)
                
                if handler.name: self.emit(Op.STORE_NAME, handler.name)
                else: self.emit(Op.POP_TOP)
                    
                for stmt in handler.body: self.visit(stmt)
                end_jumps.append(self.emit(Op.JUMP))
                self.instructions[jump_next_idx].arg = len(self.instructions)
            else:
                if handler.name: self.emit(Op.STORE_NAME, handler.name)
                else: self.emit(Op.POP_TOP)
                    
                for stmt in handler.body: self.visit(stmt)
                end_jumps.append(self.emit(Op.JUMP))

        self.emit(Op.RAISE_EXC)
        for idx in end_jumps:
            self.instructions[idx].arg = len(self.instructions)

    def visit_Expr(self, node: Expr):
        self.visit(node.value)
        self.emit(Op.POP_TOP)

    def visit_LogicalOp(self, node: LogicalOp):
        self.visit(node.left)
        self.emit(Op.DUP_TOP)
        if node.op == 'and': jump_idx = self.emit(Op.JUMP_IF_FALSE)
        else: jump_idx = self.emit(Op.JUMP_IF_TRUE)
        self.emit(Op.POP_TOP)
        self.visit(node.right)
        self.instructions[jump_idx].arg = len(self.instructions)

    def visit_UnaryOp(self, node: UnaryOp):
        self.visit(node.operand)
        if node.op == 'not': self.emit(Op.UNARY_NOT)
        elif node.op == '-': self.emit(Op.UNARY_NEGATIVE)
        elif node.op == '+': self.emit(Op.UNARY_POSITIVE)

    def visit_BinOp(self, node: BinOp):
        self.visit(node.left)
        self.visit(node.right)
        if node.op in ('+', '-', '*', '/', '//', '%', '**'): self._emit_binop(node.op)
        elif node.op == '==': self.emit(Op.CMP_EQ)
        elif node.op == '!=': self.emit(Op.CMP_NEQ)
        elif node.op == '<': self.emit(Op.CMP_LT)
        elif node.op == '>': self.emit(Op.CMP_GT)

    def visit_Assign(self, node: Assign):
        self.visit(node.value)
        if isinstance(node.target, Name):
            self.emit(Op.STORE_NAME, node.target.value)
        elif isinstance(node.target, Subscript):
            self.visit(node.target.obj); self.visit(node.target.index); self.emit(Op.STORE_INDEX)
        elif isinstance(node.target, Attribute):
            self.visit(node.target.obj); self.emit(Op.STORE_ATTR, node.target.attr)
        elif isinstance(node.target, TupleLiteral): # MODIFIED: UNPACKING
            self.emit(Op.UNPACK_SEQUENCE, len(node.target.elements))
            for el in node.target.elements:
                if isinstance(el, Name): self.emit(Op.STORE_NAME, el.value)
                elif isinstance(el, Subscript): self.visit(el.obj); self.visit(el.index); self.emit(Op.STORE_INDEX)
                elif isinstance(el, Attribute): self.visit(el.obj); self.emit(Op.STORE_ATTR, el.attr)
                else: raise SyntaxError("Cannot assign to this target inside a tuple")

    def visit_AugAssign(self, node: AugAssign):
        base_op = node.op[:-1]
        if isinstance(node.target, Name):
            self.emit(Op.LOAD_NAME, node.target.value); self.visit(node.value); self._emit_binop(base_op); self.emit(Op.STORE_NAME, node.target.value)
        elif isinstance(node.target, Subscript):
            self.visit(node.target.obj); self.visit(node.target.index); self.emit(Op.DUP_TWO); self.emit(Op.LOAD_INDEX); self.visit(node.value); self._emit_binop(base_op); self.emit(Op.STORE_INDEX)
        elif isinstance(node.target, Attribute):
            self.visit(node.target.obj); self.emit(Op.DUP_TOP); self.emit(Op.LOAD_ATTR, node.target.attr); self.visit(node.value); self._emit_binop(base_op); self.emit(Op.STORE_ATTR, node.target.attr)

    def visit_If(self, node: If):
        self.visit(node.condition)
        jump_if_false_idx = self.emit(Op.JUMP_IF_FALSE)
        for stmt in node.body: self.visit(stmt)
        if node.orelse:
            jump_end_idx = self.emit(Op.JUMP)
            self.instructions[jump_if_false_idx].arg = len(self.instructions)
            for stmt in node.orelse: self.visit(stmt)
            self.instructions[jump_end_idx].arg = len(self.instructions)
        else: self.instructions[jump_if_false_idx].arg = len(self.instructions)

    def visit_While(self, node: While):
        start_idx = len(self.instructions)
        self.visit(node.condition)
        jump_idx = self.emit(Op.JUMP_IF_FALSE)
        for stmt in node.body: self.visit(stmt)
        self.emit(Op.JUMP, start_idx)
        self.instructions[jump_idx].arg = len(self.instructions)

    def visit_For(self, node: For):
        self.visit(node.iter)
        self.emit(Op.GET_ITER)
        
        start_idx = len(self.instructions)
        jump_end_idx = self.emit(Op.FOR_ITER)
        
        if isinstance(node.target, Name):
            self.emit(Op.STORE_NAME, node.target.value)
        elif isinstance(node.target, TupleLiteral): # MODIFIED: UNPACKING in loops
            self.emit(Op.UNPACK_SEQUENCE, len(node.target.elements))
            for el in node.target.elements:
                if isinstance(el, Name): self.emit(Op.STORE_NAME, el.value)
                else: raise SyntaxError("Only simple variables supported in tuple unpacking for loops")
        else:
            raise SyntaxError("Unsupported for-loop target")
            
        for stmt in node.body: self.visit(stmt)
        self.emit(Op.JUMP, start_idx)
        self.instructions[jump_end_idx].arg = len(self.instructions)

    def visit_FunctionDef(self, node: FunctionDef):
        func_comp = Compiler()
        for stmt in node.body: func_comp.visit(stmt)
        if not func_comp.instructions or func_comp.instructions[-1].opcode != Op.RETURN_VALUE:
            func_comp.emit(Op.LOAD_CONST, None); func_comp.emit(Op.RETURN_VALUE)
        func = PyLiteFunction(node.name, node.params, func_comp.instructions)
        self.emit(Op.MAKE_FUNCTION, func)
        self.emit(Op.STORE_NAME, node.name)

    def visit_Return(self, node: Return):
        self.visit(node.value); self.emit(Op.RETURN_VALUE)

    def visit_Call(self, node: Call):
        self.visit(node.func)
        for arg in node.args: self.visit(arg)
        self.emit(Op.CALL_FUNCTION, len(node.args))

    def visit_ListLiteral(self, node: ListLiteral):
        for el in node.elements: self.visit(el)
        self.emit(Op.BUILD_LIST, len(node.elements))

    # ADDED
    def visit_TupleLiteral(self, node: TupleLiteral):
        for el in node.elements: self.visit(el)
        self.emit(Op.BUILD_TUPLE, len(node.elements))

    def visit_DictLiteral(self, node: DictLiteral):
        for k, v in zip(node.keys, node.values):
            self.visit(k); self.visit(v)
        self.emit(Op.BUILD_DICT, len(node.keys))

    def visit_Subscript(self, node: Subscript):
        self.visit(node.obj); self.visit(node.index); self.emit(Op.LOAD_INDEX)

    def visit_Slice(self, node: Slice):
        if node.lower: self.visit(node.lower)
        else: self.emit(Op.LOAD_CONST, None)
        if node.upper: self.visit(node.upper)
        else: self.emit(Op.LOAD_CONST, None)
        if node.step: self.visit(node.step)
        else: self.emit(Op.LOAD_CONST, None)
        self.emit(Op.BUILD_SLICE)

    def visit_Super(self, node: Super):
        self.emit(Op.LOAD_SUPER)

    def visit_ClassDef(self, node: ClassDef):
        if node.base: self.emit(Op.LOAD_NAME, node.base)
        methods = {}
        for stmt in node.body:
            if isinstance(stmt, FunctionDef):
                fc = Compiler()
                for s in stmt.body: fc.visit(s)
                if not fc.instructions or fc.instructions[-1].opcode != Op.RETURN_VALUE:
                    fc.emit(Op.LOAD_CONST, None); fc.emit(Op.RETURN_VALUE)
                methods[stmt.name] = PyLiteFunction(stmt.name, stmt.params, fc.instructions)
        self.emit(Op.MAKE_CLASS, (node.name, methods, bool(node.base)))
        self.emit(Op.STORE_NAME, node.name)

    def visit_Attribute(self, node: Attribute):
        self.visit(node.obj); self.emit(Op.LOAD_ATTR, node.attr)

    def visit_Import(self, node: Import):
        self.emit(Op.IMPORT_NAME, node.module); self.emit(Op.STORE_NAME, node.module)

    def visit_ImportFrom(self, node: ImportFrom):
        self.emit(Op.IMPORT_FROM, (node.module, node.names))
        for name in reversed(node.names): self.emit(Op.STORE_NAME, name)