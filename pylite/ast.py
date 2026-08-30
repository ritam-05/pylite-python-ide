from dataclasses import dataclass

class ASTNode:
    """Base class for all AST nodes."""
    pass

@dataclass
class Number(ASTNode):
    value: int

@dataclass
class Name(ASTNode):
    value: str

@dataclass
class BinOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class Assign(ASTNode):
    name: str
    value: ASTNode