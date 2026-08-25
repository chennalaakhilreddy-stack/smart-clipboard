import pyperclip
import time
import threading

clipboard_history = []
last_text = ""
running = True


def monitor_clipboard():
    global last_text

    while running:
        current_text = pyperclip.paste()

        if current_text != last_text:
            if current_text:
                clipboard_history.append(current_text)
                print(f"\nCopied: {current_text}")
                print(f"History: {len(clipboard_history)} item(s)")

            last_text = current_text

        time.sleep(0.5)


def show_history():
    print("\n--- Clipboard History ---")

    if not clipboard_history:
        print("History is empty.")
        return

    for i, item in enumerate(clipboard_history, 1):
        print(f"{i}. {item}")


def fifo():
    if clipboard_history:
        item = clipboard_history[0]
        pyperclip.copy(item)
        print(f"\nFIFO → Copied oldest item: {item}")
    else:
        print("\nHistory is empty.")


def lifo():
    if clipboard_history:
        item = clipboard_history[-1]
        pyperclip.copy(item)
        print(f"\nLIFO → Copied newest item: {item}")
    else:
        print("\nHistory is empty.")


thread = threading.Thread(target=monitor_clipboard)
thread.start()

print("Smart Clipboard is running!")
print("Commands: history | fifo | lifo | clear | exit")

while True:
    command = input("\n> ").lower().strip()

    if command == "history":
        show_history()

    elif command == "fifo":
        fifo()

    elif command == "lifo":
        lifo()

    elif command == "clear":
        clipboard_history.clear()
        print("Clipboard history cleared.")

    elif command == "exit":
        running = False
        break

    else:
        print("Unknown command.")