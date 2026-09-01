from typing import Any, Dict, List
from pylite.ast import ASTNode, Number, Boolean, Name, BinOp, Assign, Call, If, While, FunctionDef, Return

# ADDED: Our brilliant trick for stopping a function to return a value
class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class Interpreter:
    def __init__(self):
        self.environment: Dict[str, Any] = {
            "print": print
        }

    def visit(self, node: ASTNode) -> Any:
        if isinstance(node, Number):
            return self.visit_Number(node)
        elif isinstance(node, Boolean):
            return self.visit_Boolean(node)
        elif isinstance(node, Name):
            return self.visit_Name(node)
        elif isinstance(node, BinOp):
            return self.visit_BinOp(node)
        elif isinstance(node, Assign):
            return self.visit_Assign(node)
        elif isinstance(node, Call):
            return self.visit_Call(node)
        elif isinstance(node, If):
            return self.visit_If(node)
        elif isinstance(node, While):
            return self.visit_While(node)
        elif isinstance(node, FunctionDef):  # ADDED
            return self.visit_FunctionDef(node)
        elif isinstance(node, Return):       # ADDED
            return self.visit_Return(node)
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
        
        if node.op == '+': return left + right
        elif node.op == '-': return left - right
        elif node.op == '*': return left * right
        elif node.op == '==': return left == right
        elif node.op == '!=': return left != right
        elif node.op == '<': return left < right
        elif node.op == '>': return left > right
        else:
            raise Exception(f"Unknown operator: {node.op}")

    def visit_Assign(self, node: Assign) -> None:
        value = self.visit(node.value)
        self.environment[node.name] = value

    # ADDED: Store the function AST in memory so we can call it later
    def visit_FunctionDef(self, node: FunctionDef) -> None:
        self.environment[node.name] = node

    # ADDED: Throw our custom exception to break out of the function
    def visit_Return(self, node: Return) -> None:
        value = self.visit(node.value)
        raise ReturnException(value)

    def visit_Call(self, node: Call) -> Any:
        func = self.visit(node.func)
        args = [self.visit(arg) for arg in node.args]
        
        # Is it a built-in function like `print`?
        if callable(func):
            return func(*args)
            
        # Is it a PyLite function?
        elif isinstance(func, FunctionDef):
            # 1. Save the current global memory
            previous_env = self.environment
            
            # 2. Create a new local memory (inheriting globals)
            self.environment = previous_env.copy()
            
            # 3. Map the arguments to the function's parameters
            for param_name, arg_val in zip(func.params, args):
                self.environment[param_name] = arg_val
                
            # 4. Execute the function body
            try:
                for statement in func.body:
                    self.visit(statement)
                return None  # Return None if no return statement is found
            except ReturnException as ret:
                return ret.value  # Catch the returned value!
            finally:
                # 5. Restore the global memory, destroying the local variables
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