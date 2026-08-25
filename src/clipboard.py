import pyperclip
import time
import threading
from dataclasses import dataclass

from database import ClipboardDatabase


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

        # Load previously saved clipboard items.
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

        print("Clipboard monitoring started.")

    def stop_monitoring(self):
        self.running = False
        self.database.close()

    def _monitor(self):
        while self.running:
            try:
                current = pyperclip.paste()

                # Store the new clipboard content when it changes.
                if current != self.last_clipboard:
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
            # Avoid storing the same item repeatedly.
            if self.items and self.items[-1].text == text:
                return

            self.database.add_item(text)

            rows = self.database.load_items()
            item_id = rows[-1][0]

            self.items.append(
                ClipboardItem(
                    id=item_id,
                    text=text
                )
            )

        print(f"\nAdded: {text}")

    def show_history(self):
        with self.lock:
            if not self.items:
                print("\nClipboard history is empty.")
                return

            print("\nClipboard History")

            for index, item in enumerate(self.items, start=1):
                pin = "📌 " if item.pinned else ""
                preview = item.text.replace("\n", " ")

                if len(preview) > 80:
                    preview = preview[:80] + "..."

                print(f"{index}. {pin}{preview}")

    def get_item(self, index):
        with self.lock:
            if 0 <= index < len(self.items):
                return self.items[index]

            return None

    def select(self, index):
        item = self.get_item(index)

        if item is None:
            print("Invalid item number.")
            return

        pyperclip.copy(item.text)
        self.last_clipboard = item.text

        print(f"\nSelected: {item.text}")
        print("Ready to paste with Ctrl+V.")

    def delete(self, index):
        with self.lock:
            if not 0 <= index < len(self.items):
                print("Invalid item number.")
                return

            item = self.items[index]

            if item.pinned:
                print("This item is pinned. Unpin it before deleting.")
                return

            self.database.delete_item(item.id)
            self.items.pop(index)
            self._save_positions()

            print(f"Deleted: {item.text}")

    def pin(self, index):
        with self.lock:
            if not 0 <= index < len(self.items):
                print("Invalid item number.")
                return

            item = self.items[index]
            item.pinned = True

            self.database.update_pin(item.id, True)

            print(f"Pinned: {item.text}")

    def unpin(self, index):
        with self.lock:
            if not 0 <= index < len(self.items):
                print("Invalid item number.")
                return

            item = self.items[index]
            item.pinned = False

            self.database.update_pin(item.id, False)

            print(f"Unpinned: {item.text}")

    def clear(self):
        with self.lock:
            # Pinned items are kept when clearing history.
            self.database.clear_unpinned()

            self.items = [
                item for item in self.items
                if item.pinned
            ]

            self._save_positions()

            print("Cleared all unpinned items.")

    def search(self, query):
        query = query.lower().strip()

        if not query:
            print("Search query is empty.")
            return

        with self.lock:
            results = []

            for index, item in enumerate(self.items):
                if query in item.text.lower():
                    results.append((index, item))

            if not results:
                print("\nNo matching clipboard items.")
                return

            print("\nSearch Results")

            for index, item in results:
                pin = "📌 " if item.pinned else ""
                preview = item.text.replace("\n", " ")

                print(f"{index + 1}. {pin}{preview}")

    def move(self, old_index, new_index):
        with self.lock:
            if not 0 <= old_index < len(self.items):
                print("Invalid source position.")
                return

            if not 0 <= new_index < len(self.items):
                print("Invalid destination position.")
                return

            item = self.items.pop(old_index)
            self.items.insert(new_index, item)

            self._save_positions()

            print(
                f"Moved item {old_index + 1} → "
                f"position {new_index + 1}"
            )

    def _save_positions(self):
        items = [
            {"id": item.id}
            for item in self.items
        ]

        self.database.update_positions(items)

    def fifo(self):
        with self.lock:
            if not self.items:
                print("History is empty.")
                return

            print("\nFIFO")

            for item in self.items:
                print(item.text)

    def lifo(self):
        with self.lock:
            if not self.items:
                print("History is empty.")
                return

            print("\nLIFO")

            for item in reversed(self.items):
                print(item.text)

    def reverse_words(self, index):
        item = self.get_item(index)

        if item is None:
            print("Invalid item number.")
            return

        # Reverse the order of words, not individual characters.
        result = " ".join(item.text.split()[::-1])

        pyperclip.copy(result)
        self.last_clipboard = result

        print(f"\nResult: {result}")

    def uppercase(self, index):
        item = self.get_item(index)

        if item is None:
            print("Invalid item number.")
            return

        result = item.text.upper()

        pyperclip.copy(result)
        self.last_clipboard = result

        print(f"\nResult: {result}")

    def lowercase(self, index):
        item = self.get_item(index)

        if item is None:
            print("Invalid item number.")
            return

        result = item.text.lower()

        pyperclip.copy(result)
        self.last_clipboard = result

        print(f"\nResult: {result}")


def get_number(prompt):
    try:
        return int(input(prompt)) - 1
    except ValueError:
        print("Please enter a valid number.")
        return None


def print_help():
    print("""
Smart Clipboard

history
select
pin
unpin
delete
clear
search
move
fifo
lifo
reversewords
uppercase
lowercase
help
exit
""")


def main():
    clipboard = SmartClipboard()
    clipboard.start_monitoring()

    print("""
╔══════════════════════════════════════╗
║          SMART CLIPBOARD             ║
║               V1                     ║
╚══════════════════════════════════════╝

Persistent clipboard history enabled.
Type 'help' for commands.
""")

    try:
        while True:
            command = input("\n> ").strip().lower()

            if command == "history":
                clipboard.show_history()

            elif command == "select":
                clipboard.show_history()
                index = get_number("Select item: ")

                if index is not None:
                    clipboard.select(index)

            elif command == "pin":
                clipboard.show_history()
                index = get_number("Pin item: ")

                if index is not None:
                    clipboard.pin(index)

            elif command == "unpin":
                clipboard.show_history()
                index = get_number("Unpin item: ")

                if index is not None:
                    clipboard.unpin(index)

            elif command == "delete":
                clipboard.show_history()
                index = get_number("Delete item: ")

                if index is not None:
                    clipboard.delete(index)

            elif command == "clear":
                clipboard.clear()

            elif command == "search":
                query = input("Search: ")
                clipboard.search(query)

            elif command == "move":
                clipboard.show_history()

                old_index = get_number("Move item: ")
                new_index = get_number("Move to position: ")

                if old_index is not None and new_index is not None:
                    clipboard.move(old_index, new_index)

            elif command == "fifo":
                clipboard.fifo()

            elif command == "lifo":
                clipboard.lifo()

            elif command == "reversewords":
                clipboard.show_history()
                index = get_number("Transform item: ")

                if index is not None:
                    clipboard.reverse_words(index)

            elif command == "uppercase":
                clipboard.show_history()
                index = get_number("Transform item: ")

                if index is not None:
                    clipboard.uppercase(index)

            elif command == "lowercase":
                clipboard.show_history()
                index = get_number("Transform item: ")

                if index is not None:
                    clipboard.lowercase(index)

            elif command == "help":
                print_help()

            elif command == "exit":
                break

            else:
                print("Unknown command. Type 'help'.")

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        clipboard.stop_monitoring()
        print("Smart Clipboard stopped.")


if __name__ == "__main__":
    main()