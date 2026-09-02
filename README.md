# PyLite🚀

> A lightweight Python-inspired programming language, bytecode compiler, virtual machine, runtime, and desktop IDE built from scratch in Python.

PyLite aims to provide a practical subset of Python focused on **DSA, algorithms, recursion, OOP, and general programming**, without attempting to replicate the entire Python ecosystem.

## ✨ Features

* Custom **Lexer → Parser → AST → Bytecode Compiler → VM** pipeline
* Stack-based Virtual Machine
* Reference tree-walking interpreter
* Variables, integers, booleans, strings
* Lists, dictionaries, and sets
* Arithmetic and comparison operators
* `if` and `while`
* Functions, return values, and recursion
* Classes, objects, methods, `__init__`, and inheritance
* Built-ins such as `print()`, `len()`, and `set()`
* Python module interoperability
* DSA-oriented programming support
* Lightweight Tkinter desktop IDE
* File/project management
* Automatic indentation
* Light/dark mode
* Run/Stop execution
* CLI support
* Standalone Windows executable
* Automated tests with pytest

## 🧠 Architecture

```text
Source Code
    ↓
Lexer
    ↓
Parser
    ↓
AST
    ↓
Bytecode Compiler
    ↓
Bytecode
    ↓
Stack-Based VM
    ↓
Runtime
```

## 💻 Example

```python
from collections import deque

def bfs(start):
    q = deque()
    q.append(start)

    while len(q) > 0:
        node = q.popleft()
        print(node)

        if node < 4:
            q.append(node + 1)

bfs(1)
```

## 🖥️ PyLite IDE

PyLite includes a lightweight desktop IDE designed for writing, saving, organizing, and running PyLite programs.

```text
┌─────────────────────────────────────────────┐
│ PyLite IDE      Run (F5)       Theme        │
├──────────────────────┬──────────────────────┤
│                      │                      │
│     Code Editor      │   Console / Output   │
│                      │                      │
├──────────────────────┴──────────────────────┤
│ Status                                      │
└─────────────────────────────────────────────┘
```

The IDE is designed to support a lightweight project workflow with folders, files, tabs, automatic indentation, and responsive program execution.

## 📚 DSA Focus

PyLite is being developed around features required for implementing:

* Arrays and strings
* Stacks and queues
* Hash maps and sets
* Linked lists
* Trees
* Graphs
* Heaps
* Recursion
* Backtracking
* Binary search
* Dynamic programming

## 🚧 Roadmap

### Language

* `else` / `elif`
* `for` loops
* floats
* `and` / `or` / `not`
* `+=`, `-=`, `*=`, `/=`, etc.
* string operations
* slicing
* f-strings
* tuples
* unpacking
* lambda
* comprehensions

### Runtime

* `try` / `except` / `finally`
* `raise`
* `None`
* improved exceptions
* closures
* `global` / `nonlocal`
* `super()`
* magic methods
* improved iteration

### Standard Library

```text
math
collections
heapq
bisect
```

The goal is to provide lightweight, DSA-focused alternatives to commonly used Python functionality.

## 📂 Project Structure

```text
pylite-lang/
├── pylite/
│   ├── ast.py
│   ├── bytecode.py
│   ├── cli.py
│   ├── compiler.py
│   ├── gui.py
│   ├── interpreter.py
│   ├── lexer.py
│   ├── parser.py
│   └── vm.py
├── tests/
│   ├── test_dsa.py
│   └── test_interpreter.py
├── launch_ide.py
└── README.md
```

## 🎯 Vision

PyLite is not intended to replace CPython.

The goal is to build a **small, understandable, and functional Python-inspired ecosystem** with its own compiler, bytecode, VM, runtime, standard library, and lightweight IDE.

**Status: Active Development 🚀**
