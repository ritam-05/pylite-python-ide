from dataclasses import dataclass
from typing import List

class ASTNode: pass

@dataclass
class Number(ASTNode): value: int
@dataclass
class Boolean(ASTNode): value: bool
@dataclass
class Name(ASTNode): value: str
@dataclass
class BinOp(ASTNode): left: ASTNode; op: str; right: ASTNode
@dataclass
class Assign(ASTNode): target: ASTNode; value: ASTNode
@dataclass
class Call(ASTNode): func: ASTNode; args: List[ASTNode]
@dataclass
class If(ASTNode): condition: ASTNode; body: List[ASTNode]
@dataclass
class While(ASTNode): condition: ASTNode; body: List[ASTNode]
@dataclass
class FunctionDef(ASTNode): name: str; params: List[str]; body: List[ASTNode]
@dataclass
class Return(ASTNode): value: ASTNode
@dataclass
class ListLiteral(ASTNode): elements: List[ASTNode]
@dataclass
class Subscript(ASTNode): obj: ASTNode; index: ASTNode
@dataclass
class DictLiteral(ASTNode): keys: List[ASTNode]; values: List[ASTNode]

# ADDED
@dataclass
class ClassDef(ASTNode): name: str; body: List[ASTNode]
@dataclass
class Attribute(ASTNode): obj: ASTNode; attr: str
@dataclass
class Import(ASTNode): module: str
@dataclass
class ImportFrom(ASTNode): module: str; names: List[str]