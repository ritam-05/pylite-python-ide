from dataclasses import dataclass
from typing import List, Union

class ASTNode: pass

@dataclass
class Number(ASTNode): value: Union[int, float]
@dataclass
class Boolean(ASTNode): value: bool
@dataclass
class String(ASTNode): value: str
@dataclass
class Name(ASTNode): value: str
@dataclass
class BinOp(ASTNode): left: ASTNode; op: str; right: ASTNode


@dataclass
class LogicalOp(ASTNode): left: ASTNode; op: str; right: ASTNode
@dataclass
class UnaryOp(ASTNode): op: str; operand: ASTNode

@dataclass
class Expr(ASTNode): value: ASTNode

@dataclass
class Assign(ASTNode): target: ASTNode; value: ASTNode
@dataclass
class AugAssign(ASTNode): target: ASTNode; op: str; value: ASTNode
@dataclass
class Call(ASTNode): func: ASTNode; args: List[ASTNode]
@dataclass
class If(ASTNode): condition: ASTNode; body: List[ASTNode]; orelse: List[ASTNode] = None
@dataclass
class While(ASTNode): condition: ASTNode; body: List[ASTNode]
@dataclass
class For(ASTNode): target: ASTNode; iter: ASTNode; body: List[ASTNode]
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
@dataclass
class ClassDef(ASTNode): name: str; body: List[ASTNode]
@dataclass
class Attribute(ASTNode): obj: ASTNode; attr: str
@dataclass
class Import(ASTNode): module: str
@dataclass
class ImportFrom(ASTNode): module: str; names: List[str]