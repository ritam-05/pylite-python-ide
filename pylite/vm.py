from typing import Any, List, Dict
from pylite.bytecode import Op, PyLiteFunction

class CallFrame:
    def __init__(self, func: PyLiteFunction, env: Dict[str, Any]):
        self.func = func
        self.ip = 0           # Instruction Pointer
        self.env = env        # Local variables

class VM:
    def __init__(self):
        self.stack: List[Any] = []
        self.globals: Dict[str, Any] = {
            "print": print    # Native built-in
        }

    def run(self, main_func: PyLiteFunction) -> Any:
        # Create the main frame
        frames = [CallFrame(main_func, self.globals)]
        
        while frames:
            frame = frames[-1]
            
            if frame.ip >= len(frame.func.instructions):
                frames.pop()
                continue
                
            instr = frame.func.instructions[frame.ip]
            frame.ip += 1
            
            if instr.opcode == Op.LOAD_CONST:
                self.stack.append(instr.arg)
                
            elif instr.opcode == Op.LOAD_NAME:
                name = instr.arg
                if name in frame.env:
                    self.stack.append(frame.env[name])
                elif name in self.globals:
                    self.stack.append(self.globals[name])
                else:
                    raise NameError(f"name '{name}' is not defined")
                    
            elif instr.opcode == Op.STORE_NAME:
                frame.env[instr.arg] = self.stack.pop()
                
            elif instr.opcode == Op.ADD:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a + b)
                
            elif instr.opcode == Op.SUB:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a - b)
                
            elif instr.opcode == Op.MUL:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a * b)
                
            elif instr.opcode == Op.CMP_EQ:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a == b)
                
            elif instr.opcode == Op.CMP_LT:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a < b)
                
            elif instr.opcode == Op.CMP_GT:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a > b)
                
            elif instr.opcode == Op.JUMP_IF_FALSE:
                condition = self.stack.pop()
                if not condition:
                    frame.ip = instr.arg
                    
            elif instr.opcode == Op.JUMP:
                frame.ip = instr.arg
                
            elif instr.opcode == Op.MAKE_FUNCTION:
                self.stack.append(instr.arg)
                
            elif instr.opcode == Op.CALL_FUNCTION:
                arg_count = instr.arg
                args = [self.stack.pop() for _ in range(arg_count)][::-1] # Pop in reverse
                func = self.stack.pop()
                
                if callable(func):
                    # Native python function (like print)
                    result = func(*args)
                    self.stack.append(result)
                elif isinstance(func, PyLiteFunction):
                    # PyLite function -> Create new local environment and frame
                    local_env = dict(zip(func.params, args))
                    frames.append(CallFrame(func, local_env))
                else:
                    raise TypeError("Not callable")
                    
            elif instr.opcode == Op.RETURN_VALUE:
                ret_val = self.stack.pop()
                frames.pop()
                self.stack.append(ret_val) # Pass result to parent frame
                
        return self.stack.pop() if self.stack else None