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
    name: str
    value: ASTNode

@dataclass
class Call(ASTNode):
    func: ASTNode
    args: List[ASTNode]

@dataclass
class If(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

# ADDED: Represents a while loop
@dataclass
class While(ASTNode):
    condition: ASTNode
    body: List[ASTNode]