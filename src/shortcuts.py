import keyboard


class ShortcutManager:
    def __init__(self, clipboard):
        self.clipboard = clipboard
        self.fifo_hotkey = None
        self.lifo_hotkey = None

    def start(self):
        self.fifo_hotkey = keyboard.add_hotkey(
            "ctrl+shift+c",
            self.clipboard.fifo,
            suppress=True
        )

        self.lifo_hotkey = keyboard.add_hotkey(
            "ctrl+shift+l",
            self.clipboard.lifo,
            suppress=True
        )

    def stop(self):
        if self.fifo_hotkey is not None:
            keyboard.remove_hotkey(self.fifo_hotkey)

        if self.lifo_hotkey is not None:
            keyboard.remove_hotkey(self.lifo_hotkey)

        self.clipboard.disable_paste_hook()