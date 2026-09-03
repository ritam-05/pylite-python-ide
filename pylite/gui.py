import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import io
import contextlib
import traceback
import os
import datetime
import threading
import queue
import re

from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.compiler import Compiler
from pylite.vm import VM

BASE_DARK = "#1e1e1e"

THEMES = {
    "dark": {
        "bg": "#2b2b2b", "fg": "#a9b7c6", "insert": "white",
        "console_bg": "#141414", "console_fg": "#6a8759", "error_fg": "#cc6666"    
    },
    "light": {
        "bg": "#ffffff", "fg": "#000000", "insert": "black",
        "console_bg": "#f5f5f5", "console_fg": "#006600", "error_fg": "#d12424"
    }
}

class PyLiteIDE:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("1000x600") 
        self.root.configure(bg=BASE_DARK)
        
        self.font = ("Consolas", 11)
        self.current_theme = "dark"
        self.current_file = None
        
        self.output_queue = queue.Queue()
        self.is_running = False
        self.active_vm = None
        
        # MODIFIED: Event locks for thread-safe input()
        self.input_event = threading.Event()
        self.input_response = ""
        
        self.update_title()
        self._build_menu()
        self._build_ui()
        self.apply_theme()
        
        self._auto_save_loop()
        self._poll_output_queue()

    def update_title(self):
        title = "PyLite IDE"
        if self.current_file: title += f" - {os.path.basename(self.current_file)}"
        else: title += " - Untitled"
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
        toolbar = tk.Frame(self.root, bg=BASE_DARK)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        btn_style = {
            "bg": "#333333", "fg": "white", "relief": tk.FLAT, 
            "activebackground": "#555555", "activeforeground": "white",
            "font": ("Consolas", 10), "cursor": "hand2"
        }
        
        self.btn_run = tk.Button(toolbar, text="▶ Run (F5)", command=self.execute_code, **btn_style)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        self.btn_stop = tk.Button(toolbar, text="■ Stop", command=self.stop_execution, state=tk.DISABLED, **btn_style)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        btn_clear = tk.Button(toolbar, text="Clear Console", command=self.clear_console, **btn_style)
        btn_clear.pack(side=tk.LEFT, padx=5)
        self.btn_theme = tk.Button(toolbar, text="☀ Light Mode", command=self.toggle_theme, **btn_style)
        self.btn_theme.pack(side=tk.RIGHT, padx=5)
        
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=BASE_DARK, sashwidth=6, bd=0)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.editor = tk.Text(paned, font=self.font, undo=True, padx=10, pady=10, borderwidth=0, relief=tk.FLAT)
        paned.add(self.editor, stretch="always", minsize=200)
        self.editor.bind("<Return>", self._handle_return)
        
        self.console = tk.Text(paned, font=self.font, state=tk.DISABLED, padx=10, pady=10, borderwidth=0, relief=tk.FLAT)
        paned.add(self.console, stretch="always", minsize=200)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bg=BASE_DARK, fg="#888888", anchor=tk.W, font=("Consolas", 9), padx=10, pady=2)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.root.bind("<F5>", lambda event: self.execute_code())
        self.editor.insert("1.0", "# PyLite IDE\n")

    def _handle_return(self, event):
        cursor_pos = self.editor.index(tk.INSERT)
        line_num = cursor_pos.split('.')[0]
        line_text = self.editor.get(f"{line_num}.0", cursor_pos)
        indent = ""
        for char in line_text:
            if char in " \t": indent += char
            else: break
        stripped_line = line_text.strip()
        if not stripped_line and indent:
            self.editor.delete(f"{line_num}.0", cursor_pos)
            new_indent = indent[:-4] if len(indent) >= 4 else ""
            self.editor.insert(tk.INSERT, "\n" + new_indent)
            self.editor.see(tk.INSERT)
            return "break"
        if stripped_line.endswith(":"): indent += "    "
        self.editor.insert(tk.INSERT, "\n" + indent)
        self.editor.see(tk.INSERT)
        return "break"

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.btn_theme.config(text="☾ Dark Mode" if self.current_theme == "light" else "☀ Light Mode")
        self.apply_theme()

    def apply_theme(self):
        colors = THEMES[self.current_theme]
        self.editor.config(bg=colors["bg"], fg=colors["fg"], insertbackground=colors["insert"])
        self.console.config(bg=colors["console_bg"])
        self.console.tag_config("output", foreground=colors["console_fg"])
        self.console.tag_config("error", foreground=colors["error_fg"])

    def new_file(self):
        self.editor.delete("1.0", tk.END); self.current_file = None; self.update_title(); self.clear_console(); self.status_var.set("New file created.")

    def open_file(self):
        filepath = filedialog.askopenfilename(defaultextension=".py", filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if not filepath: return
        try:
            with open(filepath, "r", encoding="utf-8") as f: content = f.read()
            self.editor.delete("1.0", tk.END); self.editor.insert("1.0", content); self.current_file = filepath
            self.update_title(); self.clear_console(); self.status_var.set(f"Opened {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")

    def save_file(self):
        if not self.current_file: self.save_as_file()
        else: self._write_to_disk(self.current_file, silent=False)

    def save_as_file(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if not filepath: return
        self._write_to_disk(filepath, silent=False)

    def _write_to_disk(self, filepath, silent=True):
        try:
            content = self.editor.get("1.0", tk.END)
            if content.endswith("\n"): content = content[:-1]
            with open(filepath, "w", encoding="utf-8") as f: f.write(content)
            self.current_file = filepath
            self.update_title(); self.status_var.set(f"Auto-saved at {datetime.datetime.now().strftime('%H:%M:%S')}")
            if not silent: messagebox.showinfo("Success", "File saved successfully!")
        except Exception as e:
            if not silent: messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def _auto_save_loop(self):
        if self.current_file: self._write_to_disk(self.current_file, silent=True)
        self.root.after(5000, self._auto_save_loop)

    def write_console(self, text, is_error=False):
        colors = THEMES[self.current_theme]
        self.console.config(state=tk.NORMAL)
        self.console.tag_config("output", foreground=colors["console_fg"])
        self.console.tag_config("error", foreground=colors["error_fg"])
        if is_error: self.console.insert(tk.END, text + "\n", "error")
        else: self.console.insert(tk.END, text, "output")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def clear_console(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.config(state=tk.DISABLED)

    def _poll_output_queue(self):
        output_buffer = []
        messages_processed = 0
        finished = False

        while not self.output_queue.empty() and messages_processed < 1000:
            msg_type, msg = self.output_queue.get_nowait()
            messages_processed += 1
            
            if msg_type == "output":
                output_buffer.append(msg)
            elif msg_type == "error":
                if output_buffer:
                    self.write_console("".join(output_buffer))
                    output_buffer.clear()
                self.write_console(msg, is_error=True)
                
            # MODIFIED: Pops open a native Input Box and triggers the wait event!
            elif msg_type == "input_request":
                res = simpledialog.askstring("PyLite Input", msg, parent=self.root)
                self.input_response = res if res is not None else ""
                self.input_event.set()
                
            elif msg_type == "finish":
                finished = True
                break

        if output_buffer:
            self.write_console("".join(output_buffer))

        if finished:
            self._set_ui_state(running=False)

        self.root.after(50, self._poll_output_queue)

    def _set_ui_state(self, running):
        self.is_running = running
        if running:
            self.btn_run.config(state=tk.DISABLED); self.btn_stop.config(state=tk.NORMAL); self.status_var.set("Running...")
        else:
            self.btn_run.config(state=tk.NORMAL); self.btn_stop.config(state=tk.DISABLED); self.status_var.set("Ready"); self.active_vm = None

    def stop_execution(self):
        if self.is_running and self.active_vm:
            self.active_vm.should_stop = True
            self.status_var.set("Stopping...")
            self.input_event.set() # Unstick input if it's frozen

    def execute_code(self):
        code = self.editor.get("1.0", tk.END).strip()
        if not code or self.is_running: return
        self.clear_console(); self.write_console(f">>> Running...\n"); self._set_ui_state(running=True)
        thread = threading.Thread(target=self._run_vm_thread, args=(code,), daemon=True)
        thread.start()

    def _run_vm_thread(self, code):
        try:
            lexer = Lexer(code)
            parser = Parser(lexer.tokenize())
            ast = parser.parse()
            compiler = Compiler()
            main_func = compiler.compile(ast)
            
            # MODIFIED: Thread-safe input callback for the VM
            def gui_input(prompt=""):
                self.output_queue.put(("input_request", prompt))
                self.input_event.wait()
                self.input_event.clear()
                val = self.input_response
                self.output_queue.put(("output", f"{prompt}{val}\n"))
                return val
                
            self.active_vm = VM(
                stdout_write=lambda text: self.output_queue.put(("output", text)),
                input_cb=gui_input
            )
            self.active_vm.run(main_func)
            self.output_queue.put(("finish", None))
        except Exception as e:
            err_type = type(e).__name__
            err_msg = str(e)
            line_match = re.search(r'at line (\d+)', err_msg)
            line_str = f"Line: {line_match.group(1)}\n" if line_match else ""
            filename = os.path.basename(self.current_file) if self.current_file else "main.py"
            
            clean_traceback = f"PyLite {err_type}\n\nFile: {filename}\n{line_str}{err_type}: {err_msg}\n"
            self.output_queue.put(("error", clean_traceback))
            self.output_queue.put(("finish", None))

    def run(self):
        self.root.mainloop()