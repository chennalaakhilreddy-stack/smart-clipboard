import tkinter as tk


class ClipboardGUI:
    def __init__(self, root, clipboard):
        self.root = root
        self.clipboard = clipboard
        self.window = None
        self.search_var = None
        self.list_frame = None

    def show(self):
        if self.window is not None:
            try:
                self.window.deiconify()
                self.window.lift()
                self.window.focus_force()
                self.refresh()
                return
            except tk.TclError:
                self.window = None

        self.window = tk.Toplevel(self.root)
        self.window.title("Smart Clipboard")
        self.window.geometry("560x680")
        self.window.minsize(450, 500)
        self.window.configure(bg="#111111")

        self.build()

        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        header = tk.Frame(self.window, bg="#111111")
        header.pack(fill="x", padx=24, pady=(22, 12))

        title = tk.Label(
            header,
            text="Smart Clipboard",
            font=("Segoe UI", 21, "bold"),
            fg="white",
            bg="#111111"
        )
        title.pack(side="left")

        search_frame = tk.Frame(
            self.window,
            bg="#1d1d1d"
        )
        search_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 15)
        )

        self.search_var = tk.StringVar()

        search = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 11),
            fg="white",
            bg="#1d1d1d",
            insertbackground="white",
            relief="flat",
            bd=0
        )
        search.pack(
            fill="x",
            padx=14,
            pady=11
        )

        search.bind(
            "<KeyRelease>",
            lambda event: self.refresh()
        )

        self.list_frame = tk.Frame(
            self.window,
            bg="#111111"
        )
        self.list_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 15)
        )

        self.refresh()

    def refresh(self):
        if self.list_frame is None:
            return

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        query = ""

        if self.search_var:
            query = self.search_var.get().lower().strip()

        with self.clipboard.lock:
            items = list(self.clipboard.items)

        visible_items = []

        for index, item in enumerate(items):
            if query and query not in item.text.lower():
                continue

            visible_items.append((index, item))

        if not visible_items:
            empty = tk.Label(
                self.list_frame,
                text="No clipboard items",
                font=("Segoe UI", 11),
                fg="#777777",
                bg="#111111"
            )
            empty.pack(pady=50)
            return

        for index, item in visible_items:
            self.create_item(index, item)

    def create_item(self, index, item):
        card = tk.Frame(
            self.list_frame,
            bg="#1d1d1d"
        )
        card.pack(
            fill="x",
            pady=4
        )

        preview = item.text.replace("\n", " ")

        if len(preview) > 75:
            preview = preview[:75] + "..."

        prefix = "📌  " if item.pinned else ""

        text_button = tk.Button(
            card,
            text=prefix + preview,
            anchor="w",
            font=("Segoe UI", 10),
            fg="white",
            bg="#1d1d1d",
            activebackground="#292929",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda i=index: self.copy_item(i)
        )
        text_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(12, 4),
            pady=12
        )

        menu_button = tk.Button(
            card,
            text="⋯",
            font=("Segoe UI", 16),
            fg="#aaaaaa",
            bg="#1d1d1d",
            activebackground="#292929",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2"
        )
        menu_button.pack(
            side="right",
            padx=8
        )

        menu_button.configure(
            command=lambda i=index, b=menu_button:
            self.show_menu(i, b)
        )

    def show_menu(self, index, button):
        with self.clipboard.lock:
            if not 0 <= index < len(self.clipboard.items):
                return

            item = self.clipboard.items[index]

        menu = tk.Menu(
            self.window,
            tearoff=0,
            bg="#1d1d1d",
            fg="white",
            activebackground="#333333",
            activeforeground="white",
            bd=0
        )

        menu.add_command(
            label="Copy",
            command=lambda: self.copy_item(index)
        )

        if item.pinned:
            menu.add_command(
                label="Unpin",
                command=lambda: self.unpin(index)
            )
        else:
            menu.add_command(
                label="Pin",
                command=lambda: self.pin(index)
            )

        menu.add_separator()

        menu.add_command(
            label="Reverse Words",
            command=lambda: self.reverse_words(index)
        )

        menu.add_command(
            label="UPPERCASE",
            command=lambda: self.uppercase(index)
        )

        menu.add_command(
            label="lowercase",
            command=lambda: self.lowercase(index)
        )

        menu.add_separator()

        menu.add_command(
            label="Delete",
            command=lambda: self.delete(index)
        )

        try:
            menu.tk_popup(
                button.winfo_rootx(),
                button.winfo_rooty() + button.winfo_height()
            )
        finally:
            menu.grab_release()

    def copy_item(self, index):
        self.clipboard.select(index)

    def pin(self, index):
        self.clipboard.pin(index)
        self.refresh()

    def unpin(self, index):
        self.clipboard.unpin(index)
        self.refresh()

    def delete(self, index):
        self.clipboard.delete(index)
        self.refresh()

    def reverse_words(self, index):
        self.clipboard.reverse_words(index)
        self.refresh()

    def uppercase(self, index):
        self.clipboard.uppercase(index)
        self.refresh()

    def lowercase(self, index):
        self.clipboard.lowercase(index)
        self.refresh()

    def close(self):
        if self.window is not None:
            self.window.withdraw()