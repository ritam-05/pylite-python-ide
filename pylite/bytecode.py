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
    DIV           = auto()
    FLOORDIV      = auto()
    MOD           = auto()
    POW           = auto()
    CMP_EQ        = auto()
    CMP_NEQ       = auto()
    CMP_LT        = auto()
    CMP_GT        = auto()
    JUMP_IF_FALSE = auto()
    JUMP_IF_TRUE  = auto()
    JUMP          = auto()
    MAKE_FUNCTION = auto()
    CALL_FUNCTION = auto()
    RETURN_VALUE  = auto()
    BUILD_LIST    = auto()
    BUILD_TUPLE   = auto() # ADDED
    UNPACK_SEQUENCE = auto() # ADDED
    BUILD_DICT    = auto()
    LOAD_INDEX    = auto()
    STORE_INDEX   = auto()
    LOAD_ATTR     = auto()
    STORE_ATTR    = auto()
    MAKE_CLASS    = auto()
    IMPORT_NAME   = auto()
    IMPORT_FROM   = auto()
    DUP_TOP       = auto()
    DUP_TWO       = auto()
    POP_TOP       = auto()
    UNARY_NOT     = auto()
    UNARY_NEGATIVE = auto()
    UNARY_POSITIVE = auto()
    GET_ITER      = auto()
    FOR_ITER      = auto()
    BUILD_SLICE   = auto()
    SETUP_CATCH   = auto()
    POP_CATCH     = auto()
    RAISE_EXC     = auto()
    CHECK_EXC_MATCH = auto()
    LOAD_SUPER    = auto()

@dataclass
class Instruction:
    opcode: Op
    arg: Any = None

@dataclass
class PyLiteFunction:
    name: str
    params: List[str]
    instructions: List[Instruction]