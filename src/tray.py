import pystray
from PIL import Image, ImageDraw


class TrayManager:
    def __init__(self, clipboard, open_gui, shutdown):
        self.clipboard = clipboard
        self.open_gui = open_gui
        self.shutdown = shutdown
        self.icon = None

    def create_icon(self):
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)

        draw.rounded_rectangle(
            (8, 8, 56, 56),
            radius=12,
            fill="black"
        )

        draw.rectangle(
            (20, 16, 44, 48),
            fill="white"
        )

        draw.rectangle(
            (24, 12, 40, 20),
            fill="white"
        )

        return image

    def start(self):
        menu = pystray.Menu(
            pystray.MenuItem(
                "Open Clipboard",
                self.show_gui
            ),
            pystray.MenuItem(
                "FIFO Mode",
                self.set_fifo
            ),
            pystray.MenuItem(
                "LIFO Mode",
                self.set_lifo
            ),
            pystray.MenuItem(
                "Clear History",
                self.clear_history
            ),
            pystray.MenuItem(
                "Exit",
                self.exit
            )
        )

        self.icon = pystray.Icon(
            "SmartClipboard",
            self.create_icon(),
            "Smart Clipboard",
            menu
        )

        self.icon.run()

    def show_gui(self, icon=None, item=None):
        self.open_gui()

    def set_fifo(self, icon=None, item=None):
        self.clipboard.fifo()

    def set_lifo(self, icon=None, item=None):
        self.clipboard.lifo()

    def clear_history(self, icon=None, item=None):
        self.clipboard.clear()

    def exit(self, icon=None, item=None):
        self.shutdown()

    def stop(self):
        if self.icon:
            self.icon.stop()