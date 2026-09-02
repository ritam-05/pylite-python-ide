from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, List

class Op(Enum):
    LOAD_CONST    = auto()
    LOAD_NAME     = auto()
    STORE_NAME    = auto()
    ADD           = auto()
    SUB           = auto()
    MUL           = auto()
    DIV           = auto() # ADDED
    FLOORDIV      = auto() # ADDED
    MOD           = auto() # ADDED
    POW           = auto() # ADDED
    CMP_EQ        = auto()
    CMP_NEQ       = auto()
    CMP_LT        = auto()
    CMP_GT        = auto()
    JUMP_IF_FALSE = auto()
    JUMP          = auto()
    MAKE_FUNCTION = auto()
    CALL_FUNCTION = auto()
    RETURN_VALUE  = auto()
    BUILD_LIST    = auto()
    BUILD_DICT    = auto()
    LOAD_INDEX    = auto()
    STORE_INDEX   = auto()
    LOAD_ATTR     = auto()
    STORE_ATTR    = auto()
    MAKE_CLASS    = auto()
    IMPORT_NAME   = auto()
    IMPORT_FROM   = auto()
    DUP_TOP       = auto() # ADDED for Augmented Assignment
    DUP_TWO       = auto() # ADDED for Augmented Assignment

@dataclass
class Instruction:
    opcode: Op
    arg: Any = None

@dataclass
class PyLiteFunction:
    name: str
    params: List[str]
    instructions: List[Instruction]