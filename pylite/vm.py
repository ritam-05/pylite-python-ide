import importlib
from typing import Any, List, Dict
from pylite.bytecode import Op, PyLiteFunction

class CallFrame:
    def __init__(self, func: PyLiteFunction, env: Dict[str, Any]):
        self.func = func
        self.ip = 0
        self.env = env
        self.catch_blocks = []

class PyLiteClass:
    def __init__(self, name: str, methods: dict, base: 'PyLiteClass' = None):
        self.name = name
        self.methods = methods
        self.base = base
        
    def get_method(self, name: str):
        if name in self.methods: return self.methods[name]
        if self.base: return self.base.get_method(name)
        return None

class PyLiteInstance:
    def __init__(self, cls: PyLiteClass):
        self.cls = cls
        self.attrs = {}

class PyLiteSuper:
    def __init__(self, inst: PyLiteInstance, base_cls: PyLiteClass):
        self.inst = inst
        self.base_cls = base_cls

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
        self.stdout_write = stdout_write or (lambda text: print(text, end=""))

        def pylite_print(*args):
            out = []
            for a in args:
                if isinstance(a, PyLiteInstance):
                    res = self._call_magic(a, "__str__")
                    if res is not NotImplemented:
                        out.append(str(res))
                        continue
                out.append(str(a))
            text = " ".join(out) + "\n"
            self.stdout_write(text)
            
        def pylite_len(obj):
            if isinstance(obj, PyLiteInstance):
                res = self._call_magic(obj, "__len__")
                if res is not NotImplemented: return res
            return len(obj)

        self.globals: Dict[str, Any] = {
            "print": pylite_print,
            "len": pylite_len,
            "set": set,
            "list": list,
            "tuple": tuple,
            "range": range,
            "min": min,
            "max": max,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "IndexError": IndexError,
            "KeyError": KeyError,
            "ZeroDivisionError": ZeroDivisionError
        }

    def _call_magic(self, obj, method_name, *args):
        if not isinstance(obj, PyLiteInstance): return NotImplemented
        func = obj.cls.get_method(method_name)
        if not func: return NotImplemented
        env = dict(zip(func.params, [obj, *args]))
        return self._execute_loop([CallFrame(func, env)])

    def run(self, main_func: PyLiteFunction) -> Any:
        return self._execute_loop([CallFrame(main_func, self.globals)])

    def _execute_loop(self, frames: List[CallFrame]) -> Any:
        instruction_count = 0
        
        while frames:
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
            
            try:
                if instr.opcode == Op.LOAD_CONST: self.stack.append(instr.arg)
                elif instr.opcode == Op.LOAD_NAME:
                    name = instr.arg
                    if name in frame.env: self.stack.append(frame.env[name])
                    elif name in self.globals: self.stack.append(self.globals[name])
                    else: raise NameError(f"name '{name}' is not defined")
                elif instr.opcode == Op.STORE_NAME:
                    frame.env[instr.arg] = self.stack.pop()
                    
                # --- ARITHMETIC WITH MAGIC METHODS ---
                elif instr.opcode == Op.ADD:
                    b = self.stack.pop(); a = self.stack.pop()
                    res = self._call_magic(a, "__add__", b)
                    self.stack.append(res if res is not NotImplemented else a + b)
                elif instr.opcode == Op.SUB:
                    b = self.stack.pop(); a = self.stack.pop()
                    res = self._call_magic(a, "__sub__", b)
                    self.stack.append(res if res is not NotImplemented else a - b)
                elif instr.opcode == Op.MUL:
                    b = self.stack.pop(); a = self.stack.pop()
                    res = self._call_magic(a, "__mul__", b)
                    self.stack.append(res if res is not NotImplemented else a * b)
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
                    
                elif instr.opcode == Op.DUP_TOP: self.stack.append(self.stack[-1])
                elif instr.opcode == Op.DUP_TWO: self.stack.extend(self.stack[-2:])
                elif instr.opcode == Op.POP_TOP: self.stack.pop()
                elif instr.opcode == Op.UNARY_NOT: self.stack.append(not self.stack.pop())
                elif instr.opcode == Op.UNARY_NEGATIVE: self.stack.append(-self.stack.pop())
                elif instr.opcode == Op.UNARY_POSITIVE: self.stack.append(+self.stack.pop())

                # --- COMPARISONS WITH MAGIC METHODS ---
                elif instr.opcode == Op.CMP_EQ:
                    b = self.stack.pop(); a = self.stack.pop()
                    res = self._call_magic(a, "__eq__", b)
                    self.stack.append(res if res is not NotImplemented else a == b)
                elif instr.opcode == Op.CMP_NEQ:
                    b = self.stack.pop(); a = self.stack.pop()
                    res = self._call_magic(a, "__eq__", b)
                    self.stack.append(not res if res is not NotImplemented else a != b)
                elif instr.opcode == Op.CMP_LT:
                    b = self.stack.pop(); a = self.stack.pop()
                    res = self._call_magic(a, "__lt__", b)
                    self.stack.append(res if res is not NotImplemented else a < b)
                elif instr.opcode == Op.CMP_GT:
                    b = self.stack.pop(); a = self.stack.pop()
                    res = self._call_magic(a, "__gt__", b)
                    self.stack.append(res if res is not NotImplemented else a > b)
                    
                elif instr.opcode == Op.JUMP_IF_FALSE:
                    if not self.stack.pop(): frame.ip = instr.arg
                elif instr.opcode == Op.JUMP_IF_TRUE:
                    if self.stack.pop(): frame.ip = instr.arg
                elif instr.opcode == Op.JUMP:
                    frame.ip = instr.arg
                    
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
                elif instr.opcode == Op.BUILD_SLICE:
                    step = self.stack.pop(); upper = self.stack.pop(); lower = self.stack.pop()
                    self.stack.append(slice(lower, upper, step))

                elif instr.opcode == Op.SETUP_CATCH: frame.catch_blocks.append((instr.arg, len(self.stack)))
                elif instr.opcode == Op.POP_CATCH: frame.catch_blocks.pop()
                elif instr.opcode == Op.RAISE_EXC: raise self.stack.pop()
                elif instr.opcode == Op.CHECK_EXC_MATCH:
                    exc_type = self.stack.pop(); exc_inst = self.stack.pop()
                    self.stack.append(isinstance(exc_inst, exc_type))

                elif instr.opcode == Op.MAKE_FUNCTION:
                    self.stack.append(instr.arg)
                    
                elif instr.opcode == Op.BUILD_LIST:
                    count = instr.arg
                    self.stack.append([self.stack.pop() for _ in range(count)][::-1])
                    
                # ADDED: BUILD_TUPLE and UNPACK_SEQUENCE
                elif instr.opcode == Op.BUILD_TUPLE:
                    count = instr.arg
                    if count == 0:
                        self.stack.append(())
                    else:
                        items = [self.stack.pop() for _ in range(count)][::-1]
                        self.stack.append(tuple(items))
                        
                elif instr.opcode == Op.UNPACK_SEQUENCE:
                    count = instr.arg
                    obj = self.stack.pop()
                    items = list(obj)
                    if len(items) != count:
                        raise ValueError(f"not enough values to unpack (expected {count}, got {len(items)})")
                    for item in reversed(items):
                        self.stack.append(item)
                        
                elif instr.opcode == Op.BUILD_DICT:
                    count = instr.arg; d = {}
                    for _ in range(count):
                        v = self.stack.pop(); k = self.stack.pop()
                        d[k] = v
                    self.stack.append(d)
                    
                # --- INDEXING WITH MAGIC METHODS ---
                elif instr.opcode == Op.LOAD_INDEX:
                    idx = self.stack.pop(); obj = self.stack.pop()
                    res = self._call_magic(obj, "__getitem__", idx)
                    if res is not NotImplemented: self.stack.append(res)
                    else: self.stack.append(obj[idx])
                    
                elif instr.opcode == Op.STORE_INDEX:
                    idx = self.stack.pop(); obj = self.stack.pop(); val = self.stack.pop()
                    res = self._call_magic(obj, "__setitem__", idx, val)
                    if res is NotImplemented: obj[idx] = val

                # --- OOP & SUPER ---
                elif instr.opcode == Op.MAKE_CLASS:
                    name, methods, has_base = instr.arg
                    base_cls = self.stack.pop() if has_base else None
                    self.stack.append(PyLiteClass(name, methods, base_cls))
                    
                elif instr.opcode == Op.LOAD_SUPER:
                    inst = frame.env.get("self")
                    if not isinstance(inst, PyLiteInstance) or not inst.cls.base:
                        raise RuntimeError("super() failed: not inside derived class")
                    self.stack.append(PyLiteSuper(inst, inst.cls.base))

                elif instr.opcode == Op.LOAD_ATTR:
                    obj = self.stack.pop()
                    if isinstance(obj, PyLiteInstance):
                        if instr.arg in obj.attrs:
                            self.stack.append(obj.attrs[instr.arg])
                        else:
                            method = obj.cls.get_method(instr.arg)
                            if method: self.stack.append(BoundMethod(obj, method))
                            else: raise AttributeError(f"'{obj.cls.name}' object has no attribute '{instr.arg}'")
                    elif isinstance(obj, PyLiteSuper):
                        method = obj.base_cls.get_method(instr.arg)
                        if method: self.stack.append(BoundMethod(obj.inst, method))
                        else: raise AttributeError(f"super object has no attribute '{instr.arg}'")
                    else:
                        self.stack.append(getattr(obj, instr.arg))

                elif instr.opcode == Op.STORE_ATTR:
                    obj = self.stack.pop(); val = self.stack.pop()
                    if isinstance(obj, PyLiteInstance): obj.attrs[instr.arg] = val
                    else: setattr(obj, instr.arg, val)

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
                        init_m = func.get_method("__init__")
                        if init_m:
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
                    
            except Exception as e:
                handled = False
                while frames:
                    f = frames[-1]
                    if f.catch_blocks:
                        catch_ip, stack_len = f.catch_blocks.pop()
                        f.ip = catch_ip
                        while len(self.stack) > stack_len: self.stack.pop()
                        self.stack.append(e)
                        handled = True
                        break
                    else:
                        frames.pop()
                if not handled:
                    raise e
                    
        return self.stack.pop() if self.stack else None