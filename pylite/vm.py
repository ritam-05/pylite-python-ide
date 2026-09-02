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
    def __init__(self, stdout_write=None):
        self.stack: List[Any] = []
        self.should_stop = False
        
        # Default to standard print if no callback provided
        self.stdout_write = stdout_write or (lambda text: print(text, end=""))

        # Custom PyLite print that uses our safe callback
        def pylite_print(*args):
            text = " ".join(str(a) for a in args) + "\n"
            self.stdout_write(text)

        self.globals: Dict[str, Any] = {
            "print": pylite_print,
            "len": len,
            "set": set,
            "list": list, # Added for good measure
            "range": range
        }

    def run(self, main_func: PyLiteFunction) -> Any:
        return self._execute_loop([CallFrame(main_func, self.globals)])

    def _execute_loop(self, frames: List[CallFrame]) -> Any:
        instruction_count = 0
        
        while frames:
            # Cooperative cancellation check
            instruction_count += 1
            if instruction_count % 100 == 0 and self.should_stop:
                self.stdout_write("\n[VM] Execution terminated by user.\n")
                return None
                
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
                
            # --- ARITHMETIC OPCODES ---
            elif instr.opcode == Op.ADD:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a + b)
            elif instr.opcode == Op.SUB:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a - b)
            elif instr.opcode == Op.MUL:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a * b)
            elif instr.opcode == Op.DIV:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a / b)
            elif instr.opcode == Op.FLOORDIV:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a // b)
            elif instr.opcode == Op.MOD:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a % b)
            elif instr.opcode == Op.POW:
                b = self.stack.pop(); a = self.stack.pop()
                self.stack.append(a ** b)
                
            # --- STACK MANIPULATION ---
            elif instr.opcode == Op.DUP_TOP:
                self.stack.append(self.stack[-1])
            elif instr.opcode == Op.DUP_TWO:
                self.stack.extend(self.stack[-2:])
            elif instr.opcode == Op.POP_TOP:
                self.stack.pop()
                
            # --- UNARY OPCODES ---
            elif instr.opcode == Op.UNARY_NOT:
                self.stack.append(not self.stack.pop())
            elif instr.opcode == Op.UNARY_NEGATIVE: # MODIFIED
                self.stack.append(-self.stack.pop())
            elif instr.opcode == Op.UNARY_POSITIVE: # MODIFIED
                self.stack.append(+self.stack.pop())

            # --- COMPARISON AND CONTROL FLOW ---
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
            elif instr.opcode == Op.JUMP_IF_TRUE:
                if self.stack.pop(): frame.ip = instr.arg
            elif instr.opcode == Op.JUMP:
                frame.ip = instr.arg
                
            # --- ITERATION PROTOCOL ---
            elif instr.opcode == Op.GET_ITER:
                iterable = self.stack.pop()
                self.stack.append(iter(iterable))
            elif instr.opcode == Op.FOR_ITER:
                iterator = self.stack[-1]
                try:
                    val = next(iterator)
                    self.stack.append(val)
                except StopIteration:
                    self.stack.pop()
                    frame.ip = instr.arg
                    
            # --- SLICING ---
            elif instr.opcode == Op.BUILD_SLICE:
                step = self.stack.pop()
                upper = self.stack.pop()
                lower = self.stack.pop()
                self.stack.append(slice(lower, upper, step))

            # --- STRUCTURES AND OOP ---
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
                    self.stack.append(getattr(obj, instr.arg))

            elif instr.opcode == Op.STORE_ATTR:
                obj = self.stack.pop(); val = self.stack.pop()
                if isinstance(obj, PyLiteInstance):
                    obj.attrs[instr.arg] = val
                else:
                    setattr(obj, instr.arg, val)

            # --- IMPORTS AND CALLS ---
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
                    inst = PyLiteInstance(func)
                    self.stack.append(inst) 
                    if "__init__" in func.methods:
                        init_m = func.methods["__init__"]
                        env = dict(zip(init_m.params, [inst] + args))
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