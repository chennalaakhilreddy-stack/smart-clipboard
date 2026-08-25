import keyboard


class ShortcutManager:
    def __init__(self, clipboard):
        self.clipboard = clipboard

    def start(self):
        keyboard.add_hotkey(
            "ctrl+alt+v",
            self.copy_latest
        )

        keyboard.add_hotkey(
            "ctrl+alt+r",
            self.reverse_words
        )

        print("Global shortcuts enabled.")
        print("Ctrl+Alt+V → copy latest")
        print("Ctrl+Alt+R → reverse word order")

    def copy_latest(self):
        if self.clipboard.items:
            self.clipboard.select(
                len(self.clipboard.items) - 1
            )

    def reverse_words(self):
        if self.clipboard.items:
            self.clipboard.reverse_words(
                len(self.clipboard.items) - 1
            )

    def stop(self):
        keyboard.unhook_all()