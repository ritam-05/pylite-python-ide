from typing import Any, Dict, List
from pylite.ast import ASTNode, Number, Boolean, Name, BinOp, Assign, Call, If, While, FunctionDef, Return, ListLiteral, Subscript

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class Interpreter:
    def __init__(self):
        self.environment: Dict[str, Any] = {
            "print": print
        }

    def visit(self, node: ASTNode) -> Any:
        if isinstance(node, Number): return self.visit_Number(node)
        elif isinstance(node, Boolean): return self.visit_Boolean(node)
        elif isinstance(node, Name): return self.visit_Name(node)
        elif isinstance(node, BinOp): return self.visit_BinOp(node)
        elif isinstance(node, Assign): return self.visit_Assign(node)
        elif isinstance(node, Call): return self.visit_Call(node)
        elif isinstance(node, If): return self.visit_If(node)
        elif isinstance(node, While): return self.visit_While(node)
        elif isinstance(node, FunctionDef): return self.visit_FunctionDef(node)
        elif isinstance(node, Return): return self.visit_Return(node)
        elif isinstance(node, ListLiteral): return self.visit_ListLiteral(node) # ADDED
        elif isinstance(node, Subscript): return self.visit_Subscript(node)     # ADDED
        else: raise Exception(f"No visit method for {type(node).__name__}")

    def visit_Number(self, node: Number) -> int: return node.value
    def visit_Boolean(self, node: Boolean) -> bool: return node.value

    def visit_Name(self, node: Name) -> Any:
        name = node.value
        if name not in self.environment:
            raise NameError(f"name '{name}' is not defined")
        return self.environment[name]

    def visit_BinOp(self, node: BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        if node.op == '+': return left + right
        elif node.op == '-': return left - right
        elif node.op == '*': return left * right
        elif node.op == '==': return left == right
        elif node.op == '!=': return left != right
        elif node.op == '<': return left < right
        elif node.op == '>': return left > right
        else: raise Exception(f"Unknown operator: {node.op}")

    # MODIFIED: Handles assigning to variables AND list indices
    def visit_Assign(self, node: Assign) -> None:
        value = self.visit(node.value)
        
        if isinstance(node.target, Name):
            # Normal variable assignment: x = 10
            self.environment[node.target.value] = value
            
        elif isinstance(node.target, Subscript):
            # List index assignment: arr[0] = 10
            obj = self.visit(node.target.obj)
            index = self.visit(node.target.index)
            obj[index] = value
        else:
            raise SyntaxError("Invalid assignment target")

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        self.environment[node.name] = node

    def visit_Return(self, node: Return) -> None:
        value = self.visit(node.value)
        raise ReturnException(value)

    # ADDED: Create a Python list
    def visit_ListLiteral(self, node: ListLiteral) -> Any:
        return [self.visit(element) for element in node.elements]

    # ADDED: Access an element from a list
    def visit_Subscript(self, node: Subscript) -> Any:
        obj = self.visit(node.obj)
        index = self.visit(node.index)
        try:
            return obj[index]
        except IndexError:
            raise IndexError("List index out of range")
        except TypeError:
            raise TypeError(f"Object of type '{type(obj).__name__}' is not subscriptable")

    def visit_Call(self, node: Call) -> Any:
        func = self.visit(node.func)
        args = [self.visit(arg) for arg in node.args]
        
        if callable(func):
            return func(*args)
        elif isinstance(func, FunctionDef):
            previous_env = self.environment
            self.environment = previous_env.copy()
            for param_name, arg_val in zip(func.params, args):
                self.environment[param_name] = arg_val
            try:
                for statement in func.body:
                    self.visit(statement)
                return None
            except ReturnException as ret:
                return ret.value
            finally:
                self.environment = previous_env
        else:
            raise TypeError("Object is not callable")

    def visit_If(self, node: If) -> None:
        if self.visit(node.condition):
            for statement in node.body:
                self.visit(statement)

    def visit_While(self, node: While) -> None:
        while self.visit(node.condition):
            for statement in node.body:
                self.visit(statement)

    def interpret(self, statements: List[ASTNode]) -> Any:
        result = None
        for statement in statements:
            result = self.visit(statement)
        return result