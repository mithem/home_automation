"""StateManager manages the sqlite3 database under $DB_PATH."""
import logging
import sqlite3
from typing import Optional

import redis

import home_automation
from home_automation import config as haconfig
from home_automation import utilities

STATUS_KEYS = [
    "pulling",
    "upping",
    "downing",
    "pruning",
    "building_frontend_image",
    "pushing_frontend_image",
    "updating",
]

STATUS_DEFAULT_VALUES = [
    ("pulling", False),
    ("upping", False),
    ("downing", False),
    ("pruning", False),
    ("version", home_automation.VERSION),
    ("versionAvailable", ""),
    ("versionAvailableSince", ""),
    ("testingInitfileVersion", ""),
    ("test_email_pending", False),
    ("building_frontend_image", False),
    ("pushing_frontend_image", False),
    ("updating", False),
]

OAUTH2_DEFAULT_VALUES = [("access_token", "")]


class StateManager:
    """StateManager managing the sqlite3 database under $DB_PATH."""

    config: haconfig.Config
    rsdb: Optional[redis.Redis]

    def __init__(self, config: haconfig.Config):
        self.config = config
        self.rsdb = None
        if self.config.storage.use_redis():
            self._prepare_redis()
        else:
            self._prepare_db()

    def _prepare_redis(self):
        """Prepare redis client."""
        self.rsdb = redis.Redis(
            host=self.config.storage.redis.host,
            port=self.config.storage.redis.port,
            username=self.config.storage.redis.user,
            password=self.config.storage.redis.password,
        )

    def _prepare_db(self):
        """Prepare the DB for usage (create, initialize with default,
        repair broken values)"""
        utilities.drop_privileges(self.config)
        logging.info("Preparing DB...")
        connection = sqlite3.connect(self.config.storage.file.path)
        cur = connection.cursor()
        tables = map(
            lambda t: t[0],
            cur.execute(
                "SELECT name FROM sqlite_\
master WHERE type IN ('table', 'view')"
            ).fetchall(),
        )
        if "status" not in tables:
            self._create_status_table()
            self.reset_status()
        elif self.get_status() == {}:
            self.reset_status()
        if "oauth2" not in tables:
            self._create_oauth2_table()
            self.reset_oauth2()
        elif self.get_oauth2_credentials() == {}:
            self.reset_oauth2()
        cur.close()
        connection.close()

    def _create_status_table(self):
        """Create the table for storing status information."""
        utilities.drop_privileges(self.config)
        connection = sqlite3.connect(self.config.storage.file.path)
        cur = connection.cursor()
        cur.execute("CREATE TABLE status (key text, value text)")
        connection.commit()
        cur.close()
        connection.close()

    def _create_oauth2_table(self):
        """Create the table for storing oauth2 information."""
        utilities.drop_privileges(self.config)
        connection = sqlite3.connect(self.config.storage.file.path)
        cur = connection.cursor()
        cur.execute("CREATE TABLE oauth2 (key text, value text)")
        connection.commit()
        cur.close()
        connection.close()

    def _drop_status_table(self):
        """Drop/Delete the table for status information."""
        utilities.drop_privileges(self.config)
        connection = sqlite3.connect(self.config.storage.file.path)
        cur = connection.cursor()
        cur.execute("DROP TABLE IF EXISTS status")
        cur.close()
        connection.close()

    def _drop_oauth2_table(self):
        """Drop/Delete the table for oauth2 information."""
        utilities.drop_privileges(self.config)
        connection = sqlite3.connect(self.config.storage.file.path)
        cur = connection.cursor()
        cur.execute("DROP TABLE IF EXISTS oauth2")
        cur.close()
        connection.close()

    def _update_status_sqlite(self, key: str, status):
        """Update the status in the sqlite database."""
        assert self.config.storage.file
        try:
            utilities.drop_privileges(self.config)
            connection = sqlite3.connect(self.config.storage.file.path)
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
            self._prepare_db()
            self.update_status(key, status)

    def _update_status_redis(self, key: str, status):
        """Update the status in the redis database."""
        assert self.rsdb
        new_key = "home_automation-status-" + key
        self.rsdb.set(new_key, status)

    def update_status(self, key: str, status):
        """Change the status of the dictionary-like key-value pair."""
        if isinstance(status, int):
            status = int(status)
        if self.rsdb:
            self._update_status_redis(key, status)
        else:
            self._update_status_sqlite(key, status)

    def _update_oauth2_credentials_sqlite(self, key: str, value):
        """Change the value for the specified key in the oauth2 database."""
        assert self.config.storage.file
        try:
            utilities.drop_privileges(self.config)
            connection = sqlite3.connect(self.config.storage.file.path)
            cur = connection.cursor()
            cur.execute(
                "UPDATE oauth2 SET value=:value WHERE key=:key",
                {"key": key, "value": value},
            )
            connection.commit()
            cur.close()
            connection.close()
        except sqlite3.OperationalError:
            self._prepare_db()
            self._update_oauth2_credentials_sqlite(key, value)

    def _update_oauth2_credentials_redis(self, key: str, value):
        """Change the value for the specified key for oauth2 data in redis."""
        assert self.rsdb
        new_key = "home_automation-oauth2-" + key
        self.rsdb.set(new_key, value)

    def update_oauth2_credentials(self, key: str, value):
        """Change the value for the specified key for oauth2 data."""
        if self.rsdb:
            self._update_oauth2_credentials_redis(key, value)
        else:
            self._update_oauth2_credentials_sqlite(key, value)

    def _reset_status_sqlite(self):
        """Reset the status table."""
        utilities.drop_privileges(self.config)
        connection = sqlite3.connect(self.config.storage.file.path)
        cur = connection.cursor()
        cur.execute("DELETE FROM status WHERE true")
        cur.executemany("INSERT INTO status VALUES (?, ?)", STATUS_DEFAULT_VALUES)
        connection.commit()
        cur.close()
        connection.close()

    def _reset_status_redis(self):
        """Reset status keys in redis."""
        assert self.rsdb
        keys = self.rsdb.keys("home_automation-status-*")
        self.rsdb.delete(*keys)
        for key, value in STATUS_DEFAULT_VALUES:
            new_key = "home_automation-status-" + key
            self.rsdb.set(new_key, value)

    def reset_status(self):
        """Reset status data."""
        if self.rsdb:
            self._reset_status_redis()
        else:
            self._reset_status_sqlite()

    def reset_oauth2_sqlite(self):
        """Reset the oauth2 table."""
        utilities.drop_privileges(self.config)
        connection = sqlite3.connect(self.config.storage.file.path)
        cur = connection.cursor()
        cur.execute("DELETE FROM oauth2 WHERE true")
        cur.executemany("INSERT INTO oauth2 VALUES (?, ?)", OAUTH2_DEFAULT_VALUES)
        connection.commit()
        cur.close()
        connection.close()

    def reset_oauth2_redis(self):
        """Reset oauth2 keys in redis."""
        assert self.rsdb
        keys = self.rsdb.keys("home_automation-oauth2-*")
        self.rsdb.delete(*keys)
        for key, value in OAUTH2_DEFAULT_VALUES:
            new_key = "home_automation-oauth2-" + key
            self.rsdb.set(new_key, value)

    def reset_oauth2(self):
        """Reset oauth2 data."""
        if self.rsdb:
            self.reset_oauth2_redis()
        else:
            self.reset_oauth2_sqlite()

    def reset_db(self):
        """Reset the DB to the default values."""
        self.reset_status()
        self.reset_oauth2()

    def get_status_sqlite(self):
        """Get the status from the sqlite database."""
        try:
            utilities.drop_privileges(self.config)
            connection = sqlite3.connect(self.config.storage.file.path)
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
            self._prepare_db()
            return self.get_status()

    def get_status_redis(self):
        """Get the status from the redis database."""
        assert self.rsdb
        data = {}
        for key in STATUS_KEYS:
            new_key = "home_automation-status-" + key
            value = self.rsdb.get(new_key)
            if value:
                data[key] = bool(int(value))
            else:
                data[key] = None
        return data

    def get_status(self):
        """Return status information in the following format:

        {
            "pulling": bool,
            "upping": bool,
            "downing": bool,
            "pruning": bool,
            "building_frontend_image": bool,
            "pushing_frontend_image": bool,
            "updating": bool
        }
        """
        if self.rsdb:
            return self.get_status_redis()
        return self.get_status_sqlite()

    def get_value_sqlite(self, key: str):
        """Return the value for the corresponding key."""
        assert self.config.storage.file
        try:
            utilities.drop_privileges(self.config)
            connection = sqlite3.connect(self.config.storage.file.path)
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
            self._prepare_db()
            return self.get_value_sqlite(key)

    def get_value_redis(self, key: str):
        """Return the value for the corresponding key."""
        assert self.rsdb
        return self.rsdb.get(key)

    def get_value(self, key: str):
        """Return the value for the corresponding key."""
        if self.rsdb:
            return self.get_value_redis(key)
        return self.get_value_sqlite(key)

    def get_oauth2_credentials_sqlite(self):
        """Return oauth2 credentials as returned from the db."""
        try:
            utilities.drop_privileges(self.config)
            connection = sqlite3.connect(self.config.storage.file.path)
            cur = connection.cursor()
            keys = [pair[0] for pair in OAUTH2_DEFAULT_VALUES]
            elements = cur.execute("SELECT key, value FROM oauth2 WHERE key=?", keys)
            elems = list(elements)
            cur.close()
            connection.close()
            return elems
        except sqlite3.OperationalError:
            self._prepare_db()
            return self.get_oauth2_credentials_sqlite()

    def get_oauth2_credentials_redis(self):
        """Return oauth2 credentials as returned from the db."""
        assert self.rsdb
        data = []
        keys = ["home_automation-oauth2-" + pair[0] for pair in OAUTH2_DEFAULT_VALUES]
        for key in keys:
            data.append((key, self.rsdb.get(key)))
        return data

    def get_oauth2_credentials(self):
        """Return oauth2 credentials as returned from the db."""
        if self.rsdb:
            return self.get_oauth2_credentials_redis()
        return self.get_oauth2_credentials_sqlite()
