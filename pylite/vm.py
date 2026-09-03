import importlib
import sys
import os
import math
import collections
import heapq
import bisect
from typing import Any, List, Dict
from pylite.bytecode import Op, PyLiteFunction

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

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
    def __init__(self, func: PyLiteFunction, env: Environment, vm: 'VM'):
        self.func = func
        self.env = env
        self.vm = vm
        
    def __call__(self, *args, **kwargs):
        env_vars = self.vm._bind_args(self.func.params, list(args), kwargs)
        env = Environment(parent=self.env, initial=env_vars)
        return self.vm._execute_loop([CallFrame(self.func, env)])

class PyLiteClass:
    def __init__(self, name: str, methods: dict, base: 'PyLiteClass' = None, vm: 'VM' = None):
        self.name = name
        self.methods = methods
        self.base = base
        self.vm = vm
        
    def get_method(self, name: str):
        if name in self.methods: return self.methods[name]
        if self.base: return self.base.get_method(name)
        return None
        
    def __call__(self, *args, **kwargs):
        inst = PyLiteInstance(self, self.vm)
        init_m = self.get_method("__init__")
        if init_m:
            env_vars = self.vm._bind_args(init_m.func.params, [inst] + list(args), kwargs)
            env = Environment(parent=init_m.env, initial=env_vars)
            self.vm._execute_loop([CallFrame(init_m.func, env)])
        return inst

class PyLiteInstance:
    def __init__(self, cls: PyLiteClass, vm: 'VM'):
        self.cls = cls
        self.attrs = {}
        self.vm = vm

    def __str__(self):
        res = self.vm._call_magic(self, "__str__")
        return str(res) if res is not NotImplemented else f"<{self.cls.name} object>"
    def __repr__(self):
        res = self.vm._call_magic(self, "__repr__")
        return str(res) if res is not NotImplemented else self.__str__()
    def __len__(self):
        res = self.vm._call_magic(self, "__len__")
        if res is NotImplemented: raise TypeError(f"object of type '{self.cls.name}' has no len()")
        return int(res)
    def __lt__(self, other):
        res = self.vm._call_magic(self, "__lt__", other)
        if res is NotImplemented: raise TypeError()
        return res
    def __le__(self, other):
        res = self.vm._call_magic(self, "__le__", other)
        if res is NotImplemented: raise TypeError()
        return res
    def __gt__(self, other):
        res = self.vm._call_magic(self, "__gt__", other)
        if res is NotImplemented: raise TypeError()
        return res
    def __ge__(self, other):
        res = self.vm._call_magic(self, "__ge__", other)
        if res is NotImplemented: raise TypeError()
        return res
    def __eq__(self, other):
        res = self.vm._call_magic(self, "__eq__", other)
        if res is NotImplemented: return self is other
        return res
    def __hash__(self):
        res = self.vm._call_magic(self, "__hash__")
        if res is NotImplemented: return id(self)
        return res

class PyLiteSuper:
    def __init__(self, inst: PyLiteInstance, base_cls: PyLiteClass, vm: 'VM'):
        self.inst = inst
        self.base_cls = base_cls
        self.vm = vm

class BoundMethod:
    def __init__(self, inst, func: PyLiteClosure, vm: 'VM'):
        self.inst = inst
        self.func = func 
        self.vm = vm
        
    def __call__(self, *args, **kwargs):
        env_vars = self.vm._bind_args(self.func.func.params, [self.inst] + list(args), kwargs)
        env = Environment(parent=self.func.env, initial=env_vars)
        return self.vm._execute_loop([CallFrame(self.func.func, env)])


class VM:
    # MODIFIED: Accepts input_cb
    def __init__(self, stdout_write=None, input_cb=None):
        self.stack: List[Any] = []
        self.should_stop = False
        self.stdout_write = stdout_write or (lambda text: print(text, end=""))
        self.input_cb = input_cb or input

        def pylite_print(*args, sep=" ", end="\n"):
            text = sep.join(str(a) for a in args) + end
            self.stdout_write(text)

        # MODIFIED: Added math, input, and CP collections
        self.globals: Dict[str, Any] = {
            "print": pylite_print,
            "input": self.input_cb,
            "len": len, "set": set, "list": list, "tuple": tuple, "dict": dict,
            "int": int, "float": float, "str": str, "bool": bool,
            "range": range, "enumerate": enumerate, "zip": zip,
            "map": map, "filter": filter, "reversed": reversed, "sorted": sorted,
            "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
            "any": any, "all": all, "chr": chr, "ord": ord,
            "bin": bin, "hex": hex, "oct": oct,
            "math": math, "heapq": heapq, "bisect": bisect, "collections": collections,
            "deque": collections.deque, "Counter": collections.Counter, "defaultdict": collections.defaultdict,
            "Exception": Exception, "ValueError": ValueError, "TypeError": TypeError,
            "IndexError": IndexError, "KeyError": KeyError, "ZeroDivisionError": ZeroDivisionError
        }

    def _call_magic(self, obj, method_name, *args):
        if not isinstance(obj, PyLiteInstance): return NotImplemented
        closure = obj.cls.get_method(method_name)
        if not closure: return NotImplemented
        env = Environment(parent=closure.env, initial=dict(zip(closure.func.params, [obj, *args])))
        return self._execute_loop([CallFrame(closure.func, env)])

    def _bind_args(self, params, pos_args, kwargs):
        env_vars = {}
        p_idx = 0
        for p in params:
            if p_idx < len(pos_args):
                env_vars[p] = pos_args[p_idx]
                p_idx += 1
            elif p in kwargs:
                env_vars[p] = kwargs.pop(p)
            else:
                raise TypeError(f"Missing argument: '{p}'")
        if kwargs:
            raise TypeError(f"Unexpected keyword arguments: {list(kwargs.keys())}")
        return env_vars

    def run(self, main_func: PyLiteFunction) -> Any:
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
                    
                elif instr.opcode == Op.STORE_NAME: frame.env.vars[instr.arg] = self.stack.pop()
                elif instr.opcode == Op.STORE_GLOBAL: self.globals[instr.arg] = self.stack.pop()
                elif instr.opcode == Op.STORE_NONLOCAL: frame.env.set_nonlocal(instr.arg, self.stack.pop())
                    
                # --- ARITHMETIC ---
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

                # --- COMPARISONS ---
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
                    self.stack.append(PyLiteClosure(instr.arg, frame.env, self))
                    
                elif instr.opcode == Op.BUILD_LIST:
                    count = instr.arg
                    self.stack.append([self.stack.pop() for _ in range(count)][::-1])
                elif instr.opcode == Op.LIST_APPEND:
                    val = self.stack.pop()
                    lst = self.stack[-instr.arg]
                    lst.append(val)
                    
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
                elif instr.opcode == Op.DICT_SETITEM:
                    val = self.stack.pop()
                    key = self.stack.pop()
                    dct = self.stack[-instr.arg]
                    dct[key] = val
                    
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
                        closure_methods[m_name] = PyLiteClosure(m_func, frame.env, self)
                    self.stack.append(PyLiteClass(name, closure_methods, base_cls, self))
                    
                elif instr.opcode == Op.LOAD_SUPER:
                    inst = frame.env.get("self", self.globals)
                    if not isinstance(inst, PyLiteInstance) or not inst.cls.base:
                        raise RuntimeError("super() failed: not inside derived class")
                    self.stack.append(PyLiteSuper(inst, inst.cls.base, self))

                elif instr.opcode == Op.LOAD_ATTR:
                    obj = self.stack.pop()
                    if isinstance(obj, PyLiteInstance):
                        if instr.arg in obj.attrs:
                            self.stack.append(obj.attrs[instr.arg])
                        else:
                            method = obj.cls.get_method(instr.arg)
                            if method: self.stack.append(BoundMethod(obj, method, self))
                            else: raise AttributeError(f"'{obj.cls.name}' object has no attribute '{instr.arg}'")
                    elif isinstance(obj, PyLiteSuper):
                        method = obj.base_cls.get_method(instr.arg)
                        if method: self.stack.append(BoundMethod(obj.inst, method, self))
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

                elif instr.opcode in (Op.CALL_FUNCTION, Op.CALL_FUNCTION_KW):
                    is_kw = (instr.opcode == Op.CALL_FUNCTION_KW)
                    arg_count = instr.arg
                    kw_names = self.stack.pop() if is_kw else ()
                    
                    args = [self.stack.pop() for _ in range(arg_count)][::-1]
                    func = self.stack.pop()
                    
                    num_kwargs = len(kw_names)
                    pos_args = args[:-num_kwargs] if num_kwargs > 0 else args
                    kw_vals = args[-num_kwargs:] if num_kwargs > 0 else []
                    kwargs = dict(zip(kw_names, kw_vals))
                    
                    is_pylite_callable = isinstance(func, (PyLiteClass, BoundMethod, PyLiteClosure))
                    
                    if not is_pylite_callable and callable(func):
                        self.stack.append(func(*pos_args, **kwargs))
                    elif is_pylite_callable:
                        if isinstance(func, PyLiteClass):
                            inst = PyLiteInstance(func, self)
                            self.stack.append(inst)
                            init_m = func.get_method("__init__")
                            if init_m:
                                env_vars = self._bind_args(init_m.func.params, [inst] + pos_args, kwargs)
                                env = Environment(parent=init_m.env, initial=env_vars)
                                self._execute_loop([CallFrame(init_m.func, env)])
                        elif isinstance(func, BoundMethod):
                            env_vars = self._bind_args(func.func.func.params, [func.inst] + pos_args, kwargs)
                            env = Environment(parent=func.func.env, initial=env_vars)
                            frames.append(CallFrame(func.func.func, env))
                        elif isinstance(func, PyLiteClosure):
                            env_vars = self._bind_args(func.func.params, pos_args, kwargs)
                            env = Environment(parent=func.env, initial=env_vars)
                            frames.append(CallFrame(func.func, env))
                    else:
                        raise TypeError(f"'{type(func).__name__}' object is not callable")
                    
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