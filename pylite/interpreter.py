from typing import Any, Dict, List
from pylite.ast import ASTNode, Number, Name, BinOp, Assign

class Interpreter:
    def __init__(self):
        # The environment is our memory. It stores variables and their values.
        self.environment: Dict[str, Any] = {}

    def visit(self, node: ASTNode) -> Any:
        """Dispatch to the correct visitor method based on the node's type."""
        if isinstance(node, Number):
            return self.visit_Number(node)
        elif isinstance(node, Name):
            return self.visit_Name(node)
        elif isinstance(node, BinOp):
            return self.visit_BinOp(node)
        elif isinstance(node, Assign):
            return self.visit_Assign(node)
        else:
            raise Exception(f"No visit method for {type(node).__name__}")

    def visit_Number(self, node: Number) -> int:
        return node.value

    def visit_Name(self, node: Name) -> Any:
        name = node.value
        if name not in self.environment:
            raise NameError(f"name '{name}' is not defined")
        return self.environment[name]

    def visit_BinOp(self, node: BinOp) -> Any:
        # Evaluate the left and right sides of the tree first
        left = self.visit(node.left)
        right = self.visit(node.right)

        # Then apply the operation
        if node.op == '+':
            return left + right
        elif node.op == '*':
            return left * right
        else:
            raise Exception(f"Unknown operator: {node.op}")

    def visit_Assign(self, node: Assign) -> None:
        # Evaluate the right side (the value)
        value = self.visit(node.value)
        # Store it in memory
        self.environment[node.name] = value

    def interpret(self, statements: List[ASTNode]) -> Any:
        """Execute a list of statements and return the result of the last one."""
        result = None
        for statement in statements:
            result = self.visit(statement)
        return result