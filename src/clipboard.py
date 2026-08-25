import pyperclip
import time

clipboard_history = []
last_text = ""

print("Smart Clipboard is running...")
print("Copy items to build your history.")
print("Press Ctrl+C to stop.")

while True:
    current_text = pyperclip.paste()

    if current_text != last_text:
        if current_text:
            clipboard_history.append(current_text)
            print(f"Copied: {current_text}")
            print(f"History: {len(clipboard_history)} item(s)")

        last_text = current_text

    time.sleep(0.5)