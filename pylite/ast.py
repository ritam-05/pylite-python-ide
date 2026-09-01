from dataclasses import dataclass
from typing import List

class ASTNode:
    pass

@dataclass
class Number(ASTNode):
    value: int

@dataclass
class Boolean(ASTNode):
    value: bool

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
    target: ASTNode  # MODIFIED: Was 'name: str'. Now it can be a Name OR a Subscript!
    value: ASTNode

@dataclass
class Call(ASTNode):
    func: ASTNode
    args: List[ASTNode]

@dataclass
class If(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass
class While(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass
class FunctionDef(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]

@dataclass
class Return(ASTNode):
    value: ASTNode

# ADDED: Represents a list like [1, 2, 3]
@dataclass
class ListLiteral(ASTNode):
    elements: List[ASTNode]

# ADDED: Represents indexing like arr[0]
@dataclass
class Subscript(ASTNode):
    obj: ASTNode
    index: ASTNode