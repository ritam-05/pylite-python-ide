import importlib
from typing import Any, List, Dict
from pylite.bytecode import Op, PyLiteFunction

class CallFrame:
    def __init__(self, func: PyLiteFunction, env: Dict[str, Any]):
        self.func = func
        self.ip = 0
        self.env = env

class PyLiteClass:
    def __init__(self, name: str, methods: dict):
        self.name = name
        self.methods = methods

class PyLiteInstance:
    def __init__(self, cls: PyLiteClass):
        self.cls = cls
        self.attrs = {}

class BoundMethod:
    def __init__(self, inst, func):
        self.inst = inst
        self.func = func
    def __call__(self, *args):
        pass # VM handles this directly

class VM:
    def __init__(self):
        self.stack: List[Any] = []
        self.globals: Dict[str, Any] = {
            "print": print,
            "len": len,
            "set": set
        }

    def run(self, main_func: PyLiteFunction) -> Any:
        # We abstract the execution loop so we can run __init__ functions synchronously
        return self._execute_loop([CallFrame(main_func, self.globals)])

    def _execute_loop(self, frames: List[CallFrame]) -> Any:
        while frames:
            frame = frames[-1]
            if frame.ip >= len(frame.func.instructions):
                frames.pop()
                continue
                
            instr = frame.func.instructions[frame.ip]
            frame.ip += 1
            
            if instr.opcode == Op.LOAD_CONST: self.stack.append(instr.arg)
            elif instr.opcode == Op.LOAD_NAME:
                name = instr.arg
                if name in frame.env: self.stack.append(frame.env[name])
                elif name in self.globals: self.stack.append(self.globals[name])
                else: raise NameError(f"name '{name}' is not defined")
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
            elif instr.opcode == Op.CMP_NEQ:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a != b)
            elif instr.opcode == Op.CMP_LT:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a < b)
            elif instr.opcode == Op.CMP_GT:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a > b)
                
            elif instr.opcode == Op.JUMP_IF_FALSE:
                if not self.stack.pop(): frame.ip = instr.arg
            elif instr.opcode == Op.JUMP:
                frame.ip = instr.arg
                
            elif instr.opcode == Op.MAKE_FUNCTION:
                self.stack.append(instr.arg)
                
            elif instr.opcode == Op.BUILD_LIST:
                count = instr.arg
                lst = [self.stack.pop() for _ in range(count)][::-1]
                self.stack.append(lst)
            elif instr.opcode == Op.BUILD_DICT:
                count = instr.arg
                d = {}
                for _ in range(count):
                    v = self.stack.pop()
                    k = self.stack.pop()
                    d[k] = v
                self.stack.append(d)
                
            elif instr.opcode == Op.LOAD_INDEX:
                idx = self.stack.pop(); obj = self.stack.pop()
                self.stack.append(obj[idx])
            elif instr.opcode == Op.STORE_INDEX:
                idx = self.stack.pop(); obj = self.stack.pop(); val = self.stack.pop()
                obj[idx] = val

            # --- DSA SPECIFIC OPCODES ---
            elif instr.opcode == Op.MAKE_CLASS:
                name, methods = instr.arg
                self.stack.append(PyLiteClass(name, methods))

            elif instr.opcode == Op.LOAD_ATTR:
                obj = self.stack.pop()
                if isinstance(obj, PyLiteInstance):
                    if instr.arg in obj.attrs:
                        self.stack.append(obj.attrs[instr.arg])
                    elif instr.arg in obj.cls.methods:
                        self.stack.append(BoundMethod(obj, obj.cls.methods[instr.arg]))
                    else:
                        raise AttributeError(f"'{obj.cls.name}' object has no attribute '{instr.arg}'")
                else:
                    # Native Python object interaction (e.g. deque.append)
                    self.stack.append(getattr(obj, instr.arg))

            elif instr.opcode == Op.STORE_ATTR:
                obj = self.stack.pop(); val = self.stack.pop()
                if isinstance(obj, PyLiteInstance):
                    obj.attrs[instr.arg] = val
                else:
                    setattr(obj, instr.arg, val)

            elif instr.opcode == Op.IMPORT_NAME:
                mod = importlib.import_module(instr.arg)
                self.stack.append(mod)

            elif instr.opcode == Op.IMPORT_FROM:
                mod_name, names = instr.arg
                mod = importlib.import_module(mod_name)
                for name in names:
                    self.stack.append(getattr(mod, name))

            elif instr.opcode == Op.CALL_FUNCTION:
                arg_count = instr.arg
                args = [self.stack.pop() for _ in range(arg_count)][::-1]
                func = self.stack.pop()
                
                if isinstance(func, PyLiteClass):
                    # Instantiation
                    inst = PyLiteInstance(func)
                    self.stack.append(inst) # Push result
                    if "__init__" in func.methods:
                        init_m = func.methods["__init__"]
                        env = dict(zip(init_m.params, [inst] + args))
                        # Run __init__ cleanly in a sub-loop
                        self._execute_loop([CallFrame(init_m, env)])
                        
                elif isinstance(func, BoundMethod):
                    env = dict(zip(func.func.params, [func.inst] + args))
                    frames.append(CallFrame(func.func, env))
                    
                elif callable(func):
                    self.stack.append(func(*args))
                    
                elif isinstance(func, PyLiteFunction):
                    env = dict(zip(func.params, args))
                    frames.append(CallFrame(func, env))
                    
                else: raise TypeError("Not callable")
                
            elif instr.opcode == Op.RETURN_VALUE:
                ret_val = self.stack.pop()
                frames.pop()
                self.stack.append(ret_val)
                
        return self.stack.pop() if self.stack else None