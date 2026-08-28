import pyperclip
import time
import threading
import keyboard
import tkinter as tk

from dataclasses import dataclass

from database import ClipboardDatabase
from shortcuts import ShortcutManager
from gui import ClipboardGUI
from tray import TrayManager


@dataclass
class ClipboardItem:
    id: int
    text: str
    pinned: bool = False


class SmartClipboard:
    def __init__(self):
        self.database = ClipboardDatabase()
        self.items = []
        self.last_clipboard = ""
        self.running = False
        self.lock = threading.Lock()

        self.paste_mode = None
        self.paste_items = []
        self.paste_index = 0
        self.paste_hotkey = None
        self.ignore_clipboard_until = 0

        self.load_history()

    def load_history(self):
        rows = self.database.load_items()

        self.items = [
            ClipboardItem(
                id=row[0],
                text=row[1],
                pinned=bool(row[2])
            )
            for row in rows
        ]

    def start_monitoring(self):
        self.running = True

        thread = threading.Thread(
            target=self._monitor,
            daemon=True
        )
        thread.start()

    def stop_monitoring(self):
        self.running = False
        self.disable_paste_hook()

        try:
            self.database.close()
        except Exception:
            pass

    def _monitor(self):
        while self.running:
            try:
                current = pyperclip.paste()

                if (
                    current != self.last_clipboard
                    and time.monotonic() >= self.ignore_clipboard_until
                ):
                    self.last_clipboard = current

                    if current:
                        self.add_item(current)

            except Exception as error:
                print(f"Clipboard error: {error}")

            time.sleep(0.3)

    def add_item(self, text):
        text = text.strip()

        if not text:
            return

        with self.lock:
            if self.items and self.items[-1].text == text:
                return

            self.database.add_item(text)

            rows = self.database.load_items()

            if not rows:
                return

            item_id = rows[-1][0]

            item = ClipboardItem(
                id=item_id,
                text=text
            )

            self.items.append(item)

            if self.paste_mode:
                self.paste_items.append(text)

    def set_paste_mode(self, mode):
        self.disable_paste_hook()

        with self.lock:
            self.paste_mode = mode
            self.paste_items = []
            self.paste_index = 0

        self.enable_paste_hook()

    def enable_paste_hook(self):
        if self.paste_hotkey is None:
            self.paste_hotkey = keyboard.add_hotkey(
                "ctrl+v",
                self.smart_paste,
                suppress=True
            )

    def disable_paste_hook(self):
        if self.paste_hotkey is not None:
            try:
                keyboard.remove_hotkey(
                    self.paste_hotkey
                )
            except Exception:
                pass

            self.paste_hotkey = None

    def smart_paste(self):
        with self.lock:
            if not self.paste_mode:
                self.disable_paste_hook()

                keyboard.press_and_release("ctrl+v")
                return

            if not self.paste_items:
                return

            if self.paste_mode == "fifo":
                text = self.paste_items[
                    self.paste_index
                ]
            else:
                text = self.paste_items[
                    len(self.paste_items)
                    - 1
                    - self.paste_index
                ]

            self.paste_index += 1

            finished = (
                self.paste_index >=
                len(self.paste_items)
            )

        self.disable_paste_hook()

        pyperclip.copy(text)
        self.last_clipboard = text

        self.ignore_clipboard_until = (
            time.monotonic() + 1
        )

        time.sleep(0.05)

        keyboard.press_and_release("ctrl+v")

        if finished:
            with self.lock:
                self.paste_mode = None
                self.paste_items = []
                self.paste_index = 0
        else:
            self.enable_paste_hook()

    def show_history(self):
        with self.lock:
            if not self.items:
                print("\nClipboard history is empty.")
                return

            print("\nClipboard History")

            for index, item in enumerate(
                self.items,
                start=1
            ):
                pin = "📌 " if item.pinned else ""

                preview = item.text.replace(
                    "\n",
                    " "
                )

                if len(preview) > 80:
                    preview = preview[:80] + "..."

                print(
                    f"{index}. {pin}{preview}"
                )

    def get_item(self, index):
        with self.lock:
            if 0 <= index < len(self.items):
                return self.items[index]

            return None

    def select(self, index):
        item = self.get_item(index)

        if item is None:
            return

        pyperclip.copy(item.text)
        self.last_clipboard = item.text

    def delete(self, index):
        with self.lock:
            if not 0 <= index < len(self.items):
                return

            item = self.items[index]

            if item.pinned:
                return

            self.database.delete_item(item.id)

            self.items.pop(index)

            self._save_positions()

    def pin(self, index):
        with self.lock:
            if not 0 <= index < len(self.items):
                return

            item = self.items[index]

            if item.pinned:
                return

            item.pinned = True

            self.database.update_pin(
                item.id,
                True
            )

    def unpin(self, index):
        with self.lock:
            if not 0 <= index < len(self.items):
                return

            item = self.items[index]

            if not item.pinned:
                return

            item.pinned = False

            self.database.update_pin(
                item.id,
                False
            )

    def clear(self):
        with self.lock:
            self.database.clear_unpinned()

            self.items = [
                item
                for item in self.items
                if item.pinned
            ]

            self._save_positions()

    def search(self, query):
        query = query.lower().strip()

        if not query:
            return

        with self.lock:
            results = []

            for index, item in enumerate(
                self.items
            ):
                if query in item.text.lower():
                    results.append(
                        (index, item)
                    )

            if not results:
                print(
                    "\nNo matching clipboard items."
                )
                return

            print("\nSearch Results")

            for index, item in results:
                pin = (
                    "📌 "
                    if item.pinned
                    else ""
                )

                preview = item.text.replace(
                    "\n",
                    " "
                )

                if len(preview) > 80:
                    preview = preview[:80] + "..."

                print(
                    f"{index + 1}. "
                    f"{pin}{preview}"
                )

    def move(self, old_index, new_index):
        with self.lock:
            if not 0 <= old_index < len(self.items):
                return

            if not 0 <= new_index < len(self.items):
                return

            item = self.items.pop(old_index)

            self.items.insert(
                new_index,
                item
            )

            self._save_positions()

    def _save_positions(self):
        items = [
            {"id": item.id}
            for item in self.items
        ]

        self.database.update_positions(
            items
        )

    def fifo(self):
        self.set_paste_mode("fifo")
        print("FIFO mode")

    def lifo(self):
        self.set_paste_mode("lifo")
        print("LIFO mode")

    def reverse_words(self, index):
        item = self.get_item(index)

        if item is None:
            return

        result = " ".join(
            item.text.split()[::-1]
        )

        pyperclip.copy(result)
        self.last_clipboard = result

    def uppercase(self, index):
        item = self.get_item(index)

        if item is None:
            return

        result = item.text.upper()

        pyperclip.copy(result)
        self.last_clipboard = result

    def lowercase(self, index):
        item = self.get_item(index)

        if item is None:
            return

        result = item.text.lower()

        pyperclip.copy(result)
        self.last_clipboard = result


def main():
    clipboard = SmartClipboard()

    clipboard.start_monitoring()

    shortcuts = ShortcutManager(
        clipboard
    )

    shortcuts.start()

    root = tk.Tk()
    root.withdraw()

    gui = ClipboardGUI(
        root,
        clipboard
    )

    tray = None

    def open_gui():
        root.after(
            0,
            gui.show
        )

    def shutdown():
        root.after(
            0,
            finish
        )

    def finish():
        shortcuts.stop()
        clipboard.stop_monitoring()

        if tray:
            tray.stop()

        root.quit()

    tray = TrayManager(
        clipboard,
        open_gui,
        shutdown
    )

    tray_thread = threading.Thread(
        target=tray.start,
        daemon=True
    )

    tray_thread.start()

    try:
        root.mainloop()

    except KeyboardInterrupt:
        shutdown()

    finally:
        shortcuts.stop()
        clipboard.stop_monitoring()


if __name__ == "__main__":
    main()