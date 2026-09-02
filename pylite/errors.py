class PyLiteError(Exception):
    def __init__(self, error_type: str, message: str, line: int = 1, column: int = 1, filename: str = "main.py", source_code: str = ""):
        self.error_type = error_type
        self.message = message
        self.line = line
        self.column = column
        self.filename = filename
        self.source_code = source_code
        super().__init__(self.format_message())

    def format_message(self) -> str:
        lines = self.source_code.splitlines() if self.source_code else []
        code_line = lines[self.line - 1] if 0 < self.line <= len(lines) else ""
        pointer = " " * max(0, self.column - 1) + "^^^^^" if code_line else ""
        
        msg = f"PyLite {self.error_type}\n\n"
        msg += f"File: {self.filename}\n"
        msg += f"Line: {self.line}\n"
        msg += f"Column: {self.column}\n\n"
        if code_line:
            msg += f"    {code_line}\n"
            if pointer:
                msg += f"    {pointer}\n\n"
        msg += f"{self.error_type}: {self.message}"
        return msg