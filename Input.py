import tkinter as tk
from tkinter import simpledialog


class TimedInputDialog(simpledialog.Dialog):
    """
    A class that manages the input dialog for answering questions.
    """
    def __init__(self, parent, title, timeout=10):
        self.timeout = timeout
        super().__init__(parent, title)

    def body(self, master):
        self.label = tk.Label(master, text="Enter something:")
        self.label.pack()
        self.entry = tk.Entry(master)
        self.entry.pack()
        self.entry.focus_set()
        return self.entry

    def buttonbox(self):
        super().buttonbox()
        self.wm_attributes("-topmost", 1)
        self.timeout_event = self.after(self.timeout * 1000, self.on_timeout)

    def on_timeout(self):
        self.cancel()

    def cancel(self):
        if self.timeout_event is not None:
            self.after_cancel(self.timeout_event)
            self.timeout_event = None
        super().cancel()

    def apply(self):
        self.result = self.entry.get()


def get_input_with_timeout(timeout=10):
    """
    A function that calls and manages the input dialog for answering questions.
    """
    root = tk.Tk()
    root.withdraw()
    input_dialog = TimedInputDialog(root, "Input", timeout)
    root.destroy()
    return input_dialog.result

