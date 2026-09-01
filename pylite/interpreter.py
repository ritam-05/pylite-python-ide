from typing import Any, Dict, List
from pylite.ast import ASTNode, Number, Boolean, Name, BinOp, Assign, Call

class Interpreter:
    def __init__(self):
        self.environment: Dict[str, Any] = {
            "print": print
        }

    def visit(self, node: ASTNode) -> Any:
        if isinstance(node, Number):
            return self.visit_Number(node)
        elif isinstance(node, Boolean):    # ADDED
            return self.visit_Boolean(node)
        elif isinstance(node, Name):
            return self.visit_Name(node)
        elif isinstance(node, BinOp):
            return self.visit_BinOp(node)
        elif isinstance(node, Assign):
            return self.visit_Assign(node)
        elif isinstance(node, Call):
            return self.visit_Call(node)
        else:
            raise Exception(f"No visit method for {type(node).__name__}")

    def visit_Number(self, node: Number) -> int:
        return node.value

    def visit_Boolean(self, node: Boolean) -> bool:
        return node.value

    def visit_Name(self, node: Name) -> Any:
        name = node.value
        if name not in self.environment:
            raise NameError(f"name '{name}' is not defined")
        return self.environment[name]

    def visit_BinOp(self, node: BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)

        # Math
        if node.op == '+': return left + right
        elif node.op == '*': return left * right
        # Comparisons (ADDED)
        elif node.op == '==': return left == right
        elif node.op == '!=': return left != right
        elif node.op == '<': return left < right
        elif node.op == '>': return left > right
        else:
            raise Exception(f"Unknown operator: {node.op}")

    def visit_Assign(self, node: Assign) -> None:
        value = self.visit(node.value)
        self.environment[node.name] = value

    def visit_Call(self, node: Call) -> Any:
        func = self.visit(node.func)
        args = [self.visit(arg) for arg in node.args]
        
        if callable(func):
            return func(*args)
        else:
            raise TypeError(f"'{type(func).__name__}' object is not callable")

    def interpret(self, statements: List[ASTNode]) -> Any:
        result = None
        for statement in statements:
            result = self.visit(statement)
        return result