from typing import List, Any
from pylite.ast import *
from pylite.bytecode import Op, Instruction, PyLiteFunction

class Compiler:
    def __init__(self):
        self.instructions: List[Instruction] = []

    def emit(self, opcode: Op, arg: Any = None):
        self.instructions.append(Instruction(opcode, arg))
        return len(self.instructions) - 1  # Return index for jump patching

    def compile(self, statements: List[ASTNode]) -> PyLiteFunction:
        self.instructions = []
        for stmt in statements:
            self.visit(stmt)
        # End the main script with a return None
        self.emit(Op.LOAD_CONST, None)
        self.emit(Op.RETURN_VALUE)
        return PyLiteFunction("<main>", [], self.instructions)

    def visit(self, node: ASTNode):
        if isinstance(node, Number): self.emit(Op.LOAD_CONST, node.value)
        elif isinstance(node, Boolean): self.emit(Op.LOAD_CONST, node.value)
        elif isinstance(node, Name): self.emit(Op.LOAD_NAME, node.value)
        elif isinstance(node, BinOp): self.visit_BinOp(node)
        elif isinstance(node, Assign): self.visit_Assign(node)
        elif isinstance(node, If): self.visit_If(node)
        elif isinstance(node, While): self.visit_While(node)
        elif isinstance(node, FunctionDef): self.visit_FunctionDef(node)
        elif isinstance(node, Call): self.visit_Call(node)
        elif isinstance(node, Return): self.visit_Return(node)
        else:
            raise NotImplementedError(f"Compiler doesn't support {type(node).__name__} yet")

    def visit_BinOp(self, node: BinOp):
        self.visit(node.left)
        self.visit(node.right)
        if node.op == '+': self.emit(Op.ADD)
        elif node.op == '-': self.emit(Op.SUB)
        elif node.op == '*': self.emit(Op.MUL)
        elif node.op == '==': self.emit(Op.CMP_EQ)
        elif node.op == '!=': self.emit(Op.CMP_NEQ)
        elif node.op == '<': self.emit(Op.CMP_LT)
        elif node.op == '>': self.emit(Op.CMP_GT)

    def visit_Assign(self, node: Assign):
        self.visit(node.value)
        if isinstance(node.target, Name):
            self.emit(Op.STORE_NAME, node.target.value)

    def visit_If(self, node: If):
        self.visit(node.condition)
        jump_idx = self.emit(Op.JUMP_IF_FALSE)
        for stmt in node.body:
            self.visit(stmt)
        # Patch the jump target
        self.instructions[jump_idx].arg = len(self.instructions)

    def visit_While(self, node: While):
        start_idx = len(self.instructions)
        self.visit(node.condition)
        jump_idx = self.emit(Op.JUMP_IF_FALSE)
        
        for stmt in node.body:
            self.visit(stmt)
            
        self.emit(Op.JUMP, start_idx)
        self.instructions[jump_idx].arg = len(self.instructions)

    def visit_FunctionDef(self, node: FunctionDef):
        # We use a separate compiler for the function body
        func_compiler = Compiler()
        for stmt in node.body:
            func_compiler.visit(stmt)
        
        # Ensure the function always returns something
        if not func_compiler.instructions or func_compiler.instructions[-1].opcode != Op.RETURN_VALUE:
            func_compiler.emit(Op.LOAD_CONST, None)
            func_compiler.emit(Op.RETURN_VALUE)
            
        compiled_func = PyLiteFunction(node.name, node.params, func_compiler.instructions)
        self.emit(Op.MAKE_FUNCTION, compiled_func)
        self.emit(Op.STORE_NAME, node.name)

    def visit_Return(self, node: Return):
        self.visit(node.value)
        self.emit(Op.RETURN_VALUE)

    def visit_Call(self, node: Call):
        self.visit(node.func) # Load the function
        for arg in node.args:
            self.visit(arg)   # Load arguments
        self.emit(Op.CALL_FUNCTION, len(node.args))