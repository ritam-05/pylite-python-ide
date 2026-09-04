import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import io
import os
import datetime
import threading
import queue
import re

from pylite.lexer import Lexer
from pylite.parser import Parser
from pylite.compiler import Compiler
from pylite.vm import VM

# Professional VS Code Dark Plus Palette
VS_BG = "#1e1e1e"            # Main Editor Background
VS_SIDEBAR = "#252526"       # Explorer Sidebar Background
VS_TERMINAL = "#141414"      # Terminal / Console Background
VS_STATUS = "#007acc"        # Status Bar Blue
VS_MENU_BG = "#2d2d2d"       # Menu Bar Background
VS_MENU_FG = "#f1f1f1"       # Menu Bar Text Color

THEMES = {
    "dark": {
        "bg": VS_BG, "fg": "#d4d4d4", "insert": "#d4d4d4",
        "console_bg": VS_TERMINAL, "console_fg": "#9cdcfe", "error_fg": "#f48771",
        "error_line_bg": "#5a1d1d", "tree_bg": VS_SIDEBAR, "tree_fg": "#cccccc",
        "header_bg": VS_SIDEBAR, "header_fg": "#888888", "status_bg": VS_STATUS, "status_fg": "white",
        "menu_bg": VS_MENU_BG, "menu_fg": VS_MENU_FG
    },
    "light": {
        "bg": "#ffffff", "fg": "#000000", "insert": "black",
        "console_bg": "#f8f8f8", "console_fg": "#001080", "error_fg": "#e51400",
        "error_line_bg": "#ffcccc", "tree_bg": "#f3f3f3", "tree_fg": "#000000",
        "header_bg": "#f3f3f3", "header_fg": "#666666", "status_bg": "#007acc", "status_fg": "white",
        "menu_bg": "#f0f0f0", "menu_fg": "#000000"
    }
}

class PyLiteIDE:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("1100x650") 
        self.root.configure(bg=VS_BG)
        
        self.font = ("Consolas", 11)
        self.current_theme = "dark"
        self.current_file = None
        self.workspace_path = None
        
        self.file_states = {}
        self.output_queue = queue.Queue()
        self.is_running = False
        self.active_vm = None
        
        self.input_event = threading.Event()
        self.input_response = ""
        
        self._configure_styles()
        self.update_title()
        self._build_menu()
        self._build_ui()
        self.apply_theme()
        
        self._auto_save_loop()
        self._poll_output_queue()

    def _configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("Treeview", borderwidth=0, font=("Segoe UI", 10), rowheight=24)
        self.style.configure("Treeview.Heading", borderwidth=0)
        self.style.map('Treeview', background=[('selected', '#37373d')])

    def update_title(self):
        title = "PyLite IDE"
        if self.workspace_path: title += f" [{os.path.basename(self.workspace_path)}]"
        if self.current_file: title += f" - {os.path.basename(self.current_file)}"
        else: title += " - Untitled"
        self.root.title(title)

    def _build_menu(self):
        self.menubar = tk.Menu(self.root, tearoff=0)
        self.root.config(menu=self.menubar)
        
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Workspace...", command=self.open_workspace)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="New File", command=self.new_file, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open File...", command=self.open_file, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())

    def _build_ui(self):
        toolbar = tk.Frame(self.root, bg="#333333", height=35)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        toolbar.pack_propagate(False)
        
        btn_style = {"bg": "#333333", "fg": "#cccccc", "relief": tk.FLAT, "activebackground": "#505050", "activeforeground": "white", "font": ("Segoe UI", 9), "cursor": "hand2"}
        
        self.btn_run = tk.Button(toolbar, text="▶ Run (F5)", command=self.execute_code, **btn_style)
        self.btn_run.pack(side=tk.LEFT, padx=5, pady=4)
        self.btn_stop = tk.Button(toolbar, text="■ Stop", command=self.stop_execution, state=tk.DISABLED, **btn_style)
        self.btn_stop.pack(side=tk.LEFT, padx=5, pady=4)
        tk.Button(toolbar, text="Clear Console", command=self.clear_console, **btn_style).pack(side=tk.LEFT, padx=5, pady=4)
        self.btn_theme = tk.Button(toolbar, text="☀ Light Mode", command=self.toggle_theme, **btn_style)
        self.btn_theme.pack(side=tk.RIGHT, padx=5, pady=4)
        
        paned_main = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=VS_BG, sashwidth=4, bd=0)
        paned_main.pack(fill=tk.BOTH, expand=True)
        
        # --- EXPLORER SIDEBAR ---
        self.sidebar_frame = tk.Frame(paned_main, bg=VS_SIDEBAR)
        paned_main.add(self.sidebar_frame, stretch="never", minsize=220)
        
        self.explorer_header = tk.Frame(self.sidebar_frame, bg=VS_SIDEBAR)
        self.explorer_header.pack(fill=tk.X, side=tk.TOP, pady=5)
        
        self.lbl_explorer = tk.Label(self.explorer_header, text="EXPLORER", fg="#888888", bg=VS_SIDEBAR, font=("Segoe UI", 9, "bold"))
        self.lbl_explorer.pack(side=tk.LEFT, padx=10)
        
        icon_style = {"bg": VS_SIDEBAR, "fg": "#cccccc", "relief": tk.FLAT, "activebackground": "#37373d", "activeforeground": "white", "font": ("Segoe UI", 11), "cursor": "hand2", "width": 2}
        tk.Button(self.explorer_header, text="↻", command=self.refresh_tree, **icon_style).pack(side=tk.RIGHT, padx=2)
        tk.Button(self.explorer_header, text="📁+", command=lambda: self.create_node(is_folder=True), **icon_style).pack(side=tk.RIGHT, padx=2)
        tk.Button(self.explorer_header, text="📄+", command=lambda: self.create_node(is_folder=False), **icon_style).pack(side=tk.RIGHT, padx=2)

        self.btn_open_folder = tk.Button(self.sidebar_frame, text="Open Folder", bg="#007acc", fg="white", relief=tk.FLAT, font=("Segoe UI", 10), command=self.open_workspace, cursor="hand2")
        self.btn_open_folder.pack(pady=20, padx=20, fill=tk.X)

        self.tree = ttk.Treeview(self.sidebar_frame, show="tree")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Button-3>", self._on_tree_right_click)
        
        # --- EDITOR & TERMINAL ---
        paned_right = tk.PanedWindow(paned_main, orient=tk.VERTICAL, bg=VS_BG, sashwidth=4, bd=0)
        paned_main.add(paned_right, stretch="always", minsize=400)
        
        self.editor = tk.Text(paned_right, font=self.font, undo=True, padx=15, pady=10, borderwidth=0, relief=tk.FLAT)
        paned_right.add(self.editor, stretch="always", minsize=250)
        self.editor.bind("<Return>", self._handle_return)
        
        term_header = tk.Frame(paned_right, bg=VS_BG, height=25)
        term_header.pack_propagate(False)
        tk.Label(term_header, text="TERMINAL", fg="#cccccc", bg=VS_BG, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)
        paned_right.add(term_header, stretch="never")

        self.console = tk.Text(paned_right, font=self.font, state=tk.DISABLED, padx=15, pady=5, borderwidth=0, relief=tk.FLAT)
        paned_right.add(self.console, stretch="always", minsize=100)
        
        # --- STATUS BAR ---
        self.status_var = tk.StringVar()
        self.status_var.set(" Ready")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, anchor=tk.W, font=("Segoe UI", 9), padx=10, pady=3)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
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
            self.editor.insert(tk.INSERT, "\n" + (indent[:-4] if len(indent) >= 4 else ""))
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
        
        # Editor & Console Styling
        self.editor.config(bg=colors["bg"], fg=colors["fg"], insertbackground=colors["insert"])
        self.console.config(bg=colors["console_bg"], fg=colors["console_fg"], insertbackground=colors["insert"])
        self.console.tag_config("output", foreground=colors["console_fg"])
        self.console.tag_config("error", foreground=colors["error_fg"])
        self.editor.tag_config("error_line", background=colors["error_line_bg"])
        
        # Sidebar Styling
        self.sidebar_frame.config(bg=colors["tree_bg"])
        self.explorer_header.config(bg=colors["header_bg"])
        self.lbl_explorer.config(bg=colors["header_bg"], fg=colors["header_fg"])
        
        for widget in self.explorer_header.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(bg=colors["header_bg"], fg=colors["fg"])

        self.style.configure("Treeview", background=colors["tree_bg"], foreground=colors["tree_fg"], fieldbackground=colors["tree_bg"])
        self.status_bar.config(bg=colors["status_bg"], fg=colors["status_fg"])
        
        # Menu Bar Customization
        self.menubar.config(bg=colors["menu_bg"], fg=colors["menu_fg"])
        self.file_menu.config(bg=colors["menu_bg"], fg=colors["menu_fg"])

    # --- WORKSPACE & FILE TREE LOGIC ---
    def open_workspace(self):
        folder = filedialog.askdirectory(title="Open Workspace Folder")
        if folder:
            self.workspace_path = folder
            self.btn_open_folder.pack_forget()
            self.tree.pack(fill=tk.BOTH, expand=True)
            self.refresh_tree()
            self.update_title()
            self.status_var.set(f" Workspace: {os.path.basename(folder)}")

    def refresh_tree(self):
        open_nodes = set()
        def get_open_nodes(parent=""):
            for child in self.tree.get_children(parent):
                if self.tree.item(child, "open"): open_nodes.add(child)
                get_open_nodes(child)
        get_open_nodes()
        
        self.tree.delete(*self.tree.get_children())
        if not self.workspace_path: return
        self._populate_node("", self.workspace_path, open_nodes)

    def _populate_node(self, parent, path, open_nodes):
        try:
            for item in sorted(os.listdir(path)):
                if item.startswith('.') or item == "__pycache__": continue
                full_path = os.path.join(path, item)
                is_dir = os.path.isdir(full_path)
                text = ("📂 " if is_dir else "📄 ") + item
                is_open = full_path in open_nodes
                oid = self.tree.insert(parent, "end", full_path, text=text, open=is_open)
                if is_dir: self._populate_node(oid, full_path, open_nodes)
        except PermissionError: pass

    def get_selected_dir(self):
        if not self.workspace_path: return None
        selected = self.tree.focus()
        if not selected: return self.workspace_path
        if os.path.isdir(selected): return selected
        return os.path.dirname(selected)

    def create_node(self, is_folder=False):
        parent_dir = self.get_selected_dir()
        if not parent_dir:
            messagebox.showinfo("Notice", "Please open a workspace folder first.")
            return
            
        prompt = "Enter folder name:" if is_folder else "Enter filename (e.g. utils.py):"
        name = simpledialog.askstring("New Item", prompt, parent=self.root)
        if not name: return
        
        if not is_folder and not name.endswith('.py'): name += '.py'
        full_path = os.path.join(parent_dir, name)
        
        try:
            if is_folder:
                os.mkdir(full_path)
                self.refresh_tree()
                # FIXED: Check if the parent is a visible tree node before expanding
                if self.tree.exists(parent_dir):
                    self.tree.item(parent_dir, open=True)
            else:
                with open(full_path, 'w', encoding='utf-8') as f: f.write("# PyLite IDE\n")
                self.refresh_tree()
                
                # FIXED: Check if the parent is a visible tree node before expanding
                if self.tree.exists(parent_dir):
                    self.tree.item(parent_dir, open=True)
                
                # Safely select and focus the new file
                if self.tree.exists(full_path):
                    self.tree.selection_set(full_path)
                    self.tree.focus(full_path)
                    
                self._open_specific_file(full_path)
        except Exception as e: 
            messagebox.showerror("Error", str(e))
            
    def _on_tree_right_click(self, event):
        if not self.workspace_path: return
        item = self.tree.identify_row(event.y)
        if item: 
            self.tree.selection_set(item)
            self.tree.focus(item)
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="New File Here", command=lambda: self.create_node(is_folder=False))
        menu.add_command(label="New Folder Here", command=lambda: self.create_node(is_folder=True))
        menu.add_separator()
        menu.add_command(label="Refresh", command=self.refresh_tree)
        menu.post(event.x_root, event.y_root)

    def _on_tree_select(self, event):
        item = self.tree.focus()
        if not item or os.path.isdir(item): return
        self._open_specific_file(item)

    def _open_specific_file(self, filepath):
        if self.current_file == filepath: return
        
        if self.current_file:
            self._write_to_disk(self.current_file, silent=True)
            self.file_states[self.current_file] = {
                "cursor": self.editor.index(tk.INSERT),
                "scroll": self.editor.yview()
            }
        else:
            content = self.editor.get("1.0", tk.END).strip()
            if content and content != "# PyLite IDE":
                if messagebox.askyesno("Save", "Save untitled file before switching?"):
                    self.save_as_file()
                    
        try:
            with open(filepath, "r", encoding="utf-8") as f: content = f.read()
            
            self.editor.config(undo=False)
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", content)
            self.editor.config(undo=True)
            
            self.current_file = filepath
            self.update_title()
            self.editor.tag_remove("error_line", "1.0", tk.END)
            self.status_var.set(f" Opened {os.path.basename(filepath)}")
            
            state = self.file_states.get(filepath)
            if state:
                self.editor.mark_set(tk.INSERT, state["cursor"])
                self.editor.yview_moveto(state["scroll"][0])
            else:
                self.editor.mark_set(tk.INSERT, "1.0")
                self.editor.see("1.0")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open:\n{e}")

    # --- STANDARD FILE I/O ---
    def new_file(self):
        if self.workspace_path:
            self.create_node(is_folder=False)
        else:
            filepath = filedialog.asksaveasfilename(title="Create New File", defaultextension=".py", filetypes=[("Python Files", "*.py")])
            if not filepath: return
            try:
                with open(filepath, "w", encoding="utf-8") as f: f.write("# PyLite IDE\n")
                self._open_specific_file(filepath)
            except Exception as e: messagebox.showerror("Error", str(e))

    def open_file(self):
        filepath = filedialog.askopenfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if filepath: self._open_specific_file(filepath)

    def save_file(self):
        if not self.current_file: self.save_as_file()
        else: self._write_to_disk(self.current_file, silent=False)

    def save_as_file(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if filepath: self._write_to_disk(filepath, silent=False)

    def _write_to_disk(self, filepath, silent=True):
        try:
            content = self.editor.get("1.0", tk.END)
            if content.endswith("\n"): content = content[:-1]
            with open(filepath, "w", encoding="utf-8") as f: f.write(content)
            self.current_file = filepath
            self.update_title(); self.status_var.set(f" Auto-saved at {datetime.datetime.now().strftime('%H:%M:%S')}")
            if not silent: messagebox.showinfo("Success", "File saved successfully!")
        except Exception as e:
            if not silent: messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def _auto_save_loop(self):
        if self.current_file: self._write_to_disk(self.current_file, silent=True)
        self.root.after(5000, self._auto_save_loop)

    # --- EXECUTION & CONSOLE ---
    def write_console(self, text, is_error=False):
        colors = THEMES[self.current_theme]
        self.console.config(state=tk.NORMAL)
        if is_error: self.console.insert(tk.END, text + "\n", "error")
        else: self.console.insert(tk.END, text, "output")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def clear_console(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.config(state=tk.DISABLED)
        self.editor.tag_remove("error_line", "1.0", tk.END)

    def _poll_output_queue(self):
        output_buffer = []; finished = False
        while not self.output_queue.empty() and len(output_buffer) < 1000:
            msg_type, msg = self.output_queue.get_nowait()
            if msg_type == "output": output_buffer.append(msg)
            elif msg_type == "error":
                if output_buffer: self.write_console("".join(output_buffer)); output_buffer.clear()
                self.write_console(msg, is_error=True)
            elif msg_type == "error_highlight":
                self.editor.tag_add("error_line", f"{msg}.0", f"{msg}.end")
            elif msg_type == "input_request":
                res = simpledialog.askstring("PyLite Input", msg, parent=self.root)
                self.input_response = res if res is not None else ""
                self.input_event.set()
            elif msg_type == "finish": finished = True; break

        if output_buffer: self.write_console("".join(output_buffer))
        if finished: self._set_ui_state(running=False)
        self.root.after(50, self._poll_output_queue)

    def _set_ui_state(self, running):
        self.is_running = running
        if running:
            self.btn_run.config(state=tk.DISABLED); self.btn_stop.config(state=tk.NORMAL); self.status_var.set(" Running...")
        else:
            self.btn_run.config(state=tk.NORMAL); self.btn_stop.config(state=tk.DISABLED); self.status_var.set(" Ready"); self.active_vm = None

    def stop_execution(self):
        if self.is_running and self.active_vm:
            self.active_vm.should_stop = True
            self.status_var.set(" Stopping...")
            self.input_event.set()

    def execute_code(self):
        code = self.editor.get("1.0", tk.END).strip()
        if not code or self.is_running: return
        self.clear_console(); self.write_console(f">>> Running...\n"); self._set_ui_state(running=True)
        if self.current_file: os.chdir(os.path.dirname(os.path.abspath(self.current_file)))
        threading.Thread(target=self._run_vm_thread, args=(code,), daemon=True).start()

    def _run_vm_thread(self, code):
        try:
            lexer = Lexer(code)
            parser = Parser(lexer.tokenize())
            ast = parser.parse()
            compiler = Compiler()
            main_func = compiler.compile(ast)
            
            def gui_input(prompt=""):
                self.output_queue.put(("input_request", prompt))
                self.input_event.wait()
                self.input_event.clear()
                val = self.input_response
                self.output_queue.put(("output", f"{prompt}{val}\n"))
                return val
                
            self.active_vm = VM(stdout_write=lambda text: self.output_queue.put(("output", text)), input_cb=gui_input)
            self.active_vm.run(main_func)
            self.output_queue.put(("finish", None))
        except Exception as e:
            err_type = type(e).__name__
            err_msg = str(e)
            line_match = re.search(r'at line (\d+)', err_msg)
            if line_match: self.output_queue.put(("error_highlight", int(line_match.group(1))))
                
            line_str = f"Line: {line_match.group(1)}\n" if line_match else ""
            filename = os.path.basename(self.current_file) if self.current_file else "main.py"
            clean_traceback = f"PyLite {err_type}\n\nFile: {filename}\n{line_str}{err_type}: {err_msg}\n"
            self.output_queue.put(("error", clean_traceback))
            self.output_queue.put(("finish", None))

    def run(self):
        self.root.mainloop()