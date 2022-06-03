"""StateManager manages the sqlite3 database under $DB_PATH."""
import sqlite3
import logging

import home_automation
from home_automation import config as haconfig

CONFIG = haconfig.load_config()
STATUS_KEYS = ["pulling", "upping", "downing", "pruning"]


class StateManager:
    """StateManager managing the sqlite3 database under $DB_PATH."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.prepare_db()

    def prepare_db(self):
        """Prepare the DB for usage (create, initialize with default,
        repair broken values)"""
        logging.info("Preparing DB...")
        connection = sqlite3.connect(self.db_path)
        cur = connection.cursor()
        tables = map(
            lambda t: t[0],
            cur.execute(
                "SELECT name FROM sqlite_\
master WHERE type IN ('table', 'view')"
            ).fetchall(),
        )
        if "status" not in tables:
            self.create_status_table()
            self.reset_status()
        elif self.get_status() == {}:
            self.reset_status()
        if "oauth2" not in tables:
            self.create_oauth2_table()
            self.reset_oauth2()
        elif self.get_oauth2_credentials() == {}:
            self.reset_oauth2()
        cur.close()
        connection.close()

    def create_status_table(self):
        """Create the table for storing status information."""
        connection = sqlite3.connect(self.db_path)
        cur = connection.cursor()
        cur.execute("CREATE TABLE status (key text, value text)")
        connection.commit()
        cur.close()
        connection.close()

    def create_oauth2_table(self):
        """Create the table for storing oauth2 information."""
        connection = sqlite3.connect(self.db_path)
        cur = connection.cursor()
        cur.execute("CREATE TABLE oauth2 (key text, value text)")
        connection.commit()
        cur.close()
        connection.close()

    def drop_status_table(self):
        """Drop/Delete the table for status information."""
        connection = sqlite3.connect(self.db_path)
        cur = connection.cursor()
        cur.execute("DROP TABLE IF EXISTS status")
        cur.close()
        connection.close()

    def drop_oauth2_table(self):
        """Drop/Delete the table for oauth2 information."""
        connection = sqlite3.connect(self.db_path)
        cur = connection.cursor()
        cur.execute("DROP TABLE IF EXISTS oauth2")
        cur.close()
        connection.close()

    def update_status(self, key: str, status):
        """Change the status of the dictionary-like key-value pair."""
        try:
            connection = sqlite3.connect(self.db_path)
            cur = connection.cursor()
            cur.execute(
                "UPDATE status SET value=:status WH\
ERE key=:key",
                {"key": key, "status": status},
            )
            connection.commit()
            cur.close()
            connection.close()
        except sqlite3.OperationalError:
            self.prepare_db()
            self.update_status(key, status)

    def update_oauth2_credentials(self, key: str, value):
        """Change the value for the specified key in the oauth2 database."""
        try:
            connection = sqlite3.connect(self.db_path)
            cur = connection.cursor()
            cur.execute(
                "UPDATE oauth2 SET value=:value WHERE key=:key",
                {"key": key, "value": value},
            )
            connection.commit()
            cur.close()
            connection.close()
        except sqlite3.OperationalError:
            self.prepare_db()
            self.update_oauth2_credentials(key, value)

    def reset_status(self):
        """Reset the status table."""
        default_values = [
            ("pulling", False),
            ("upping", False),
            ("downing", False),
            ("pruning", False),
            ("version", home_automation.VERSION),
            ("versionAvailable", ""),
            ("versionAvailableSince", ""),
            ("testingInitfileVersion", ""),
            ("test_email_pending", False),
        ]
        connection = sqlite3.connect(self.db_path)
        cur = connection.cursor()
        cur.execute("DELETE FROM status WHERE true")
        cur.executemany("INSERT INTO status VALUES (?, ?)", default_values)
        connection.commit()
        cur.close()
        connection.close()

    def reset_oauth2(self):
        """Reset the oauth2 table."""
        default_values = [("access_token", "")]
        connection = sqlite3.connect(self.db_path)
        cur = connection.cursor()
        cur.execute("DELETE FROM oauth2 WHERE true")
        cur.executemany("INSERT INTO oauth2 VALUES (?, ?)", default_values)
        connection.commit()
        cur.close()
        connection.close()

    def reset_db(self):
        """Reset the DB to the default values."""
        self.reset_status()
        self.reset_oauth2()

    def get_status(self):
        """Return status information in the following format:

        {
            "pulling": bool,
            "upping": bool,
            "downing": bool,
            "pruning": bool
        }
        """
        try:
            connection = sqlite3.connect(self.db_path)
            cur = connection.cursor()
            data = {}
            elements = cur.execute("SELECT key, value FROM status").fetchall()
            for elem in elements:
                if elem[0] in STATUS_KEYS:
                    data[elem[0]] = bool(int(elem[1]))
            cur.close()
            connection.close()
            return data
        except sqlite3.OperationalError:
            self.prepare_db()
            return self.get_status()

    def get_value(self, key: str):
        """Return the value for the corresponding key."""
        try:
            connection = sqlite3.connect(self.db_path)
            cur = connection.cursor()
            elements = cur.execute("SELECT key, value FROM status WHERE key=?", [key])
            elems = list(elements)
            cur.close()
            connection.close()
            if len(elems) == 0:
                return None
            if len(elems) == 1:
                return elems[0][1]  # each element: (key, value)
            # I know, the db will already by reset, but "reset db" is ambiguous
            self.reset_db()
            raise Exception("Multiple elements found for the same key. Resetting db.")
        except sqlite3.OperationalError:
            self.prepare_db()
            return self.get_value(key)

    def get_oauth2_credentials(self):
        """Return oauth2 credentials as returned from the db."""
        try:
            connection = sqlite3.connect(self.db_path)
            cur = connection.cursor()
            keys = ["access_token"]
            elements = cur.execute("SELECT key, value FROM oauth2 WHERE key=?", keys)
            elems = list(elements)
            cur.close()
            connection.close()
            return elems
        except sqlite3.OperationalError:
            self.prepare_db()
            return self.get_oauth2_credentials()

    def execute(self, sql: str, *params, commit=False):
        """Execute an arbitrary SQL statement and return the result.
        If `commit`, commit the connection.
        Additional params will be passed to `cursor.execute`.
        Take care of SQL injections for yourself."""
        connection = sqlite3.connect(self.db_path)
        cur = connection.cursor()
        elements = list(cur.execute(sql, *params))
        if commit:
            connection.commit()
        cur.close()
        connection.close()
        return elements
