from dataclasses import dataclass
from typing import List

class ASTNode:
    pass

@dataclass
class Number(ASTNode):
    value: int

@dataclass
class Boolean(ASTNode):
    value: bool  # ADDED: Represents True or False

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