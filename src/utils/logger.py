import os
import sqlite3
from datetime import datetime


class EventLogger:
    def __init__(self, database_path="logs/events.sqlite3"):
        self.database_path = str(database_path)
        dossier = os.path.dirname(self.database_path)
        if dossier != "" and not os.path.exists(dossier):
            os.makedirs(dossier)

        connection = sqlite3.connect(self.database_path)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS events "
            "(id INTEGER PRIMARY KEY, date TEXT NOT NULL, type TEXT NOT NULL, details TEXT)"
        )
        connection.commit()
        connection.close()

    def log(self, event_type, details=""):
        date = datetime.now().isoformat(timespec="seconds")
        connection = sqlite3.connect(self.database_path)
        connection.execute(
            "INSERT INTO events (date, type, details) VALUES (?, ?, ?)",
            (date, event_type, details),
        )
        connection.commit()
        connection.close()

    def get_events(self):
        connection = sqlite3.connect(self.database_path)
        rows = connection.execute(
            "SELECT date, type, details FROM events ORDER BY id"
        ).fetchall()
        connection.close()

        events = []
        for row in rows:
            events.append({"date": row[0], "type": row[1], "details": row[2]})
        return events
