import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import io
import contextlib
import traceback

from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.compiler import Compiler
from pylite.vm import VM

class PyLiteIDE:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyLite IDE")
        self.root.geometry("800x600")
        
        # Configure fonts and colors
        self.font = ("Consolas", 12)
        self.bg_color = "#1e1e1e"
        self.fg_color = "#d4d4d4"
        self.console_bg = "#000000"
        
        self.current_file = None
        self._build_ui()

    def _build_ui(self):
        # Top Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        btn_run = ttk.Button(toolbar, text="▶ Run (F5)", command=self.execute_code)
        btn_run.pack(side=tk.LEFT, padx=2)
        
        btn_clear = ttk.Button(toolbar, text="Clear Console", command=self.clear_console)
        btn_clear.pack(side=tk.LEFT, padx=2)
        
        # Main PanedWindow (Splitter)
        paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Code Editor
        self.editor = tk.Text(paned, font=self.font, bg=self.bg_color, fg=self.fg_color, insertbackground="white")
        paned.add(self.editor, weight=3)
        
        # Output Console
        self.console = tk.Text(paned, font=self.font, bg=self.console_bg, fg="#00ff00", state=tk.DISABLED)
        paned.add(self.console, weight=1)
        
        # Key bindings
        self.root.bind("<F5>", lambda event: self.execute_code())
        
        # Pre-fill with a sample DSA program
        sample_code = """# PyLite DSA Test
from collections import deque

def bfs(start):
    q = deque()
    q.append(start)
    visited = {start: True}
    
    while len(q) > 0:
        node = q.popleft()
        print("Visited:", node)
        
        next_node = node + 1
        if next_node < 4:
            q.append(next_node)

bfs(1)
"""
        self.editor.insert("1.0", sample_code)

    def write_console(self, text, is_error=False):
        self.console.config(state=tk.NORMAL)
        if is_error:
            self.console.insert(tk.END, text + "\n", "error")
            self.console.tag_config("error", foreground="red")
        else:
            self.console.insert(tk.END, text)
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def clear_console(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.config(state=tk.DISABLED)

    def execute_code(self):
        code = self.editor.get("1.0", tk.END).strip()
        if not code:
            return
            
        self.write_console(f">>> Running...\n")
        
        # Capture stdout to redirect `print()` to our GUI console
        output_buffer = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(output_buffer):
                lexer = Lexer(code)
                parser = Parser(lexer.tokenize())
                ast = parser.parse()
                
                compiler = Compiler()
                main_func = compiler.compile(ast)
                
                vm = VM()
                vm.run(main_func)
                
            # Write captured output to GUI
            self.write_console(output_buffer.getvalue())
            self.write_console(">>> Finished successfully.\n\n")
            
        except Exception as e:
            # If an error happens, write it in red
            err_msg = traceback.format_exc()
            self.write_console(err_msg, is_error=True)

    def run(self):
        self.root.mainloop()