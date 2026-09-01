from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, List

class Op(Enum):
    LOAD_CONST    = auto() # Push a literal value
    LOAD_NAME     = auto() # Push a variable's value
    STORE_NAME    = auto() # Pop a value and store it
    ADD           = auto() # Pop 2, add, push
    SUB           = auto() # Pop 2, subtract, push
    MUL           = auto() # Pop 2, multiply, push
    CMP_EQ        = auto() # Pop 2, compare (==), push
    CMP_NEQ       = auto() # Pop 2, compare (!=), push
    CMP_LT        = auto() # Pop 2, compare (<), push
    CMP_GT        = auto() # Pop 2, compare (>), push
    JUMP_IF_FALSE = auto() # Pop 1. If false, jump to arg
    JUMP          = auto() # Unconditionally jump to arg
    MAKE_FUNCTION = auto() # Create a function object
    CALL_FUNCTION = auto() # Call a function with `arg` arguments
    RETURN_VALUE  = auto() # Return from a function

@dataclass
class Instruction:
    opcode: Op
    arg: Any = None
    
    def __repr__(self):
        return f"{self.opcode.name:<15} {self.arg if self.arg is not None else ''}"

@dataclass
class PyLiteFunction:
    name: str
    params: List[str]
    instructions: List[Instruction]