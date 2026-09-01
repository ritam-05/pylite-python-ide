from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.compiler import Compiler
from pylite.vm import VM

def run_pylite(code: str):
    lexer = Lexer(code)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    compiler = Compiler()
    main_func = compiler.compile(ast)
    vm = VM()
    vm.run(main_func)

def test_dsa_linked_list(capsys):
    code = """
class Node:
    def __init__(self, val):
        self.val = val
        self.next = 0

head = Node(1)
head.next = Node(2)
head.next.next = Node(3)

curr = head
while curr != 0:
    print(curr.val)
    curr = curr.next
"""
    run_pylite(code)
    assert capsys.readouterr().out == "1\n2\n3\n"

def test_dsa_imports_and_bfs(capsys):
    # Using python's native deque from our VM!
    code = """
from collections import deque

def bfs(start):
    q = deque()
    q.append(start)
    
    while len(q) > 0:
        node = q.popleft()
        print(node)
        if node < 3:
            q.append(node + 1)

bfs(1)
"""
    run_pylite(code)
    assert capsys.readouterr().out == "1\n2\n3\n"