import importlib
from typing import Any, List, Dict
from pylite.bytecode import Op, PyLiteFunction

class Environment:
    def __init__(self, parent=None, initial=None):
        self.vars = initial if initial is not None else {}
        self.parent = parent
        
    def get(self, name, vm_globals):
        if name in self.vars: return self.vars[name]
        if self.parent: return self.parent.get(name, vm_globals)
        if name in vm_globals: return vm_globals[name]
        raise NameError(f"name '{name}' is not defined")
        
    def set_nonlocal(self, name, val):
        if self.parent and self.parent._set_nonlocal(name, val): return
        raise SyntaxError(f"no binding for nonlocal '{name}' found")
        
    def _set_nonlocal(self, name, val):
        if name in self.vars:
            self.vars[name] = val
            return True
        if self.parent:
            return self.parent._set_nonlocal(name, val)
        return False

class CallFrame:
    def __init__(self, func: PyLiteFunction, env: Environment):
        self.func = func
        self.ip = 0
        self.env = env
        self.catch_blocks = []

class PyLiteClosure:
    def __init__(self, func: PyLiteFunction, env: Environment):
        self.func = func
        self.env = env

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
    def __call__(self, *args): pass

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
        closure = obj.cls.get_method(method_name)
        if not closure: return NotImplemented
        env = Environment(parent=closure.env, initial=dict(zip(closure.func.params, [obj, *args])))
        return self._execute_loop([CallFrame(closure.func, env)])

    def run(self, main_func: PyLiteFunction) -> Any:
        # At top level, self.vars IS self.globals. STORE_NAME natively writes to global!
        env = Environment(parent=None, initial=self.globals)
        return self._execute_loop([CallFrame(main_func, env)])

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
                    self.stack.append(frame.env.get(instr.arg, self.globals))
                    
                # Variable Storage Scopes
                elif instr.opcode == Op.STORE_NAME: frame.env.vars[instr.arg] = self.stack.pop()
                elif instr.opcode == Op.STORE_GLOBAL: self.globals[instr.arg] = self.stack.pop()
                elif instr.opcode == Op.STORE_NONLOCAL: frame.env.set_nonlocal(instr.arg, self.stack.pop())
                    
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

                # --- CLOSURES AND OOP ---
                elif instr.opcode == Op.MAKE_FUNCTION:
                    # Upgrade function to a closure bound to the current environment!
                    self.stack.append(PyLiteClosure(instr.arg, frame.env))
                    
                elif instr.opcode == Op.BUILD_LIST:
                    count = instr.arg
                    self.stack.append([self.stack.pop() for _ in range(count)][::-1])
                elif instr.opcode == Op.BUILD_TUPLE:
                    count = instr.arg
                    if count == 0: self.stack.append(())
                    else: self.stack.append(tuple([self.stack.pop() for _ in range(count)][::-1]))
                elif instr.opcode == Op.UNPACK_SEQUENCE:
                    count = instr.arg
                    obj = list(self.stack.pop())
                    if len(obj) != count: raise ValueError(f"not enough values to unpack (expected {count}, got {len(obj)})")
                    for item in reversed(obj): self.stack.append(item)
                elif instr.opcode == Op.BUILD_DICT:
                    count = instr.arg; d = {}
                    for _ in range(count):
                        v = self.stack.pop(); k = self.stack.pop()
                        d[k] = v
                    self.stack.append(d)
                    
                elif instr.opcode == Op.LOAD_INDEX:
                    idx = self.stack.pop(); obj = self.stack.pop()
                    res = self._call_magic(obj, "__getitem__", idx)
                    if res is not NotImplemented: self.stack.append(res)
                    else: self.stack.append(obj[idx])
                    
                elif instr.opcode == Op.STORE_INDEX:
                    idx = self.stack.pop(); obj = self.stack.pop(); val = self.stack.pop()
                    res = self._call_magic(obj, "__setitem__", idx, val)
                    if res is NotImplemented: obj[idx] = val

                elif instr.opcode == Op.MAKE_CLASS:
                    name, methods, has_base = instr.arg
                    base_cls = self.stack.pop() if has_base else None
                    
                    closure_methods = {}
                    for m_name, m_func in methods.items():
                        closure_methods[m_name] = PyLiteClosure(m_func, frame.env)
                        
                    self.stack.append(PyLiteClass(name, closure_methods, base_cls))
                    
                elif instr.opcode == Op.LOAD_SUPER:
                    inst = frame.env.get("self", self.globals)
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
                            env = Environment(parent=init_m.env, initial=dict(zip(init_m.func.params, [inst] + args)))
                            self._execute_loop([CallFrame(init_m.func, env)])
                            
                    elif isinstance(func, BoundMethod):
                        env = Environment(parent=func.func.env, initial=dict(zip(func.func.func.params, [func.inst] + args)))
                        frames.append(CallFrame(func.func.func, env))
                        
                    elif callable(func):
                        self.stack.append(func(*args))
                        
                    elif isinstance(func, PyLiteClosure):
                        env = Environment(parent=func.env, initial=dict(zip(func.func.params, args)))
                        frames.append(CallFrame(func.func, env))
                        
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