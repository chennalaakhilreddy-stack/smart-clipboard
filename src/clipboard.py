import pyperclip
import time

last_text = ""

print("Smart Clipboard is running...")
print("Copy something to test it. Press Ctrl+C to stop.")

while True:
    current_text = pyperclip.paste()

    if current_text != last_text:
        if current_text:
            print("Copied:", current_text)
            last_text = current_text

    time.sleep(0.5)