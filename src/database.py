import sqlite3
from pathlib import Path


class ClipboardDatabase:
    def __init__(self, db_path="clipboard.db"):
        self.db_path = Path(db_path)
        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )
        self.create_table()

    def create_table(self):
        # Create the table the first time the app runs.
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                pinned INTEGER DEFAULT 0,
                position INTEGER NOT NULL
            )
        """)
        self.connection.commit()

    def load_items(self):
        cursor = self.connection.execute("""
            SELECT id, text, pinned, position
            FROM clipboard_items
            ORDER BY position ASC
        """)
        return cursor.fetchall()

    def add_item(self, text, pinned=False, position=None):
        if position is None:
            cursor = self.connection.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 "
                "FROM clipboard_items"
            )
            position = cursor.fetchone()[0]

        self.connection.execute("""
            INSERT INTO clipboard_items (text, pinned, position)
            VALUES (?, ?, ?)
        """, (text, int(pinned), position))

        self.connection.commit()

    def update_pin(self, item_id, pinned):
        self.connection.execute("""
            UPDATE clipboard_items
            SET pinned = ?
            WHERE id = ?
        """, (int(pinned), item_id))

        self.connection.commit()

    def delete_item(self, item_id):
        self.connection.execute(
            "DELETE FROM clipboard_items WHERE id = ?",
            (item_id,)
        )
        self.connection.commit()

    def clear_unpinned(self):
        self.connection.execute(
            "DELETE FROM clipboard_items WHERE pinned = 0"
        )
        self.connection.commit()

    def update_positions(self, items):
        for position, item in enumerate(items):
            self.connection.execute("""
                UPDATE clipboard_items
                SET position = ?
                WHERE id = ?
            """, (position, item["id"]))

        self.connection.commit()

    def close(self):
        self.connection.close()