import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import io
import contextlib
import traceback
import os

from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.compiler import Compiler
from pylite.vm import VM

# Define our color palettes
THEMES = {
    "dark": {
        "bg": "#2b2b2b",
        "fg": "#a9b7c6",
        "insert": "white",
        "console_bg": "#1e1e1e",
        "console_fg": "#6a8759", # Soft green
        "error_fg": "#cc6666"    # Soft red
    },
    "light": {
        "bg": "#ffffff",
        "fg": "#000000",
        "insert": "black",
        "console_bg": "#f5f5f5",
        "console_fg": "#006600",
        "error_fg": "#d12424"
    }
}

class PyLiteIDE:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("1000x600") # Wider default window for side-by-side
        
        self.font = ("Consolas", 11)
        self.current_theme = "dark"
        self.current_file = None
        
        self.update_title()
        self._build_menu()
        self._build_ui()
        self.apply_theme()
        
        # Start the background auto-save loop (runs every 5000ms / 5 seconds)
        self._auto_save_loop()

    def update_title(self):
        title = "PyLite IDE"
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        else:
            title += " - Untitled"
        self.root.title(title)

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())

    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        btn_run = ttk.Button(toolbar, text="▶ Run (F5)", command=self.execute_code)
        btn_run.pack(side=tk.LEFT, padx=2)
        
        btn_clear = ttk.Button(toolbar, text="Clear Console", command=self.clear_console)
        btn_clear.pack(side=tk.LEFT, padx=2)
        
        self.btn_theme = ttk.Button(toolbar, text="☀ Light Mode", command=self.toggle_theme)
        self.btn_theme.pack(side=tk.RIGHT, padx=2)
        
        # Main Splitter - Now HORIZONTAL for RStudio feel
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Code Editor (Left)
        self.editor = tk.Text(paned, font=self.font, undo=True, padx=10, pady=10, borderwidth=0)
        paned.add(self.editor, weight=1)
        
        # Output Console (Right)
        self.console = tk.Text(paned, font=self.font, state=tk.DISABLED, padx=10, pady=10, borderwidth=0)
        paned.add(self.console, weight=1)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.root.bind("<F5>", lambda event: self.execute_code())
        
        sample_code = """# PyLite
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

    def toggle_theme(self):
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.btn_theme.config(text="☾ Dark Mode")
        else:
            self.current_theme = "dark"
            self.btn_theme.config(text="☀ Light Mode")
        self.apply_theme()

    def apply_theme(self):
        colors = THEMES[self.current_theme]
        self.editor.config(bg=colors["bg"], fg=colors["fg"], insertbackground=colors["insert"])
        self.console.config(bg=colors["console_bg"])
        # Update existing text tags if any exist
        self.console.tag_config("output", foreground=colors["console_fg"])
        self.console.tag_config("error", foreground=colors["error_fg"])

    # --- FILE OPERATIONS ---
    def new_file(self):
        self.editor.delete("1.0", tk.END)
        self.current_file = None
        self.update_title()
        self.clear_console()
        self.status_var.set("New file created.")

    def open_file(self):
        filepath = filedialog.askopenfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if not filepath:
            return
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", content)
            self.current_file = filepath
            self.update_title()
            self.clear_console()
            self.status_var.set(f"Opened {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")

    def save_file(self):
        if not self.current_file:
            self.save_as_file()
        else:
            self._write_to_disk(self.current_file, silent=False)

    def save_as_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        self._write_to_disk(filepath, silent=False)

    def _write_to_disk(self, filepath, silent=True):
        try:
            content = self.editor.get("1.0", tk.END)
            if content.endswith("\n"):
                content = content[:-1]
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.current_file = filepath
            self.update_title()
            
            # Show the time of the last save in the status bar
            import datetime
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.status_var.set(f"Auto-saved at {time_str}")
            
            if not silent:
                messagebox.showinfo("Success", "File saved successfully!")
        except Exception as e:
            if not silent:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def _auto_save_loop(self):
        # If there is a file associated, save it silently
        if self.current_file:
            self._write_to_disk(self.current_file, silent=True)
        
        # Schedule this function to run again in 5000 milliseconds
        self.root.after(5000, self._auto_save_loop)

    # --- CONSOLE & EXECUTION ---
    def write_console(self, text, is_error=False):
        colors = THEMES[self.current_theme]
        self.console.config(state=tk.NORMAL)
        
        # Ensure tags exist
        self.console.tag_config("output", foreground=colors["console_fg"])
        self.console.tag_config("error", foreground=colors["error_fg"])
        
        if is_error:
            self.console.insert(tk.END, text + "\n", "error")
        else:
            self.console.insert(tk.END, text, "output")
            
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
            
        self.clear_console()
        self.write_console(f">>> Running...\n")
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
                
            self.write_console(output_buffer.getvalue())
            self.write_console("\n>>> Finished successfully.\n")
            
        except Exception as e:
            err_msg = traceback.format_exc()
            self.write_console(err_msg, is_error=True)

    def run(self):
        self.root.mainloop()