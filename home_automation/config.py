"""Everything to do with configuration."""
from typing import Any, List, Dict, Optional, Union
import yaml


class ConfigEmail:
    """Email configuration."""
    address: str
    password: str

    def __init__(self, address: str, password: str):
        self.address = address
        self.password = password

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.address == other.address and
            self.password == other.password
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'address': self.address,
            'password': self.password
        }


class ConfigHomeAssistant:
    """Home Assistant configuration."""
    token: Optional[str]
    url: Optional[str]
    insecure_https: bool

    def __init__(self, data: Dict[str, Union[str, bool]]):
        self.token = str(data.get("token"))
        self.url = str(data.get("url"))
        self.insecure_https = bool(data.get("insecure_https", False))

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.token == other.token and
            self.url == other.url and
            self.insecure_https == other.insecure_https
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'token': self.token,
            'insecure_https': self.insecure_https
        }


class ConfigPortainer:
    """Portainer configuration."""
    url: Optional[str]
    username: Optional[str]
    password: Optional[str]
    home_assistant_env: Optional[str]
    home_assistant_stack: Optional[str]
    insecure_https: bool

    def __init__(self, data: Dict[str, Union[str, bool]]):
        self.url = str(data.get("url"))
        self.username = str(data.get("username"))
        self.password = str(data.get("password"))
        self.home_assistant_env = str(data.get(
            "home_assistant_env",
            data.get("home_assistant_endpoint")
        ))
        self.home_assistant_stack = str(data.get("home_assistant_stack"))
        self.insecure_https = bool(data.get("insecure_https", False))

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.url == other.url and
            self.username == other.username and
            self.password == other.password and
            self.home_assistant_env == other.home_assistant_env and
            self.home_assistant_stack == other.home_assistant_stack and
            self.insecure_https == other.insecure_https
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'username': self.username,
            'password': self.password,
            'home_assistant_env': self.home_assistant_env,
            'home_assistant_stack': self.home_assistant_stack,
            'insecure_https': self.insecure_https
        }


class ConfigThingsServer:
    """Things server configuration."""
    url: Optional[str]
    insecure_https: bool

    def __init__(self, data: Dict[str, Union[str, bool]]):
        self.url = str(data.get("url"))
        self.insecure_https = bool(data.get("insecure_https", False))

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.url == other.url and
            self.insecure_https == other.insecure_https
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'insecure_https': self.insecure_https
        }


class ConfigProcess:
    """Configuration of the home_automation process."""
    user: Optional[str]
    group: Optional[str]

    def __init__(self, data: Dict[str, str]):
        self.user = data.get("user")
        self.group = data.get("group")

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.user == other.user and
            self.group == other.group
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'user': self.user,
            'group': self.group
        }


class ConfigRunner:  # pylint: disable=too-few-public-methods
    """home_automation.runner configuration."""
    cron_user: Optional[str]

    def __init__(self, data: Dict[str, str]):
        cron_user = data.get("cron_user")
        self.cron_user = cron_user

    def __eq__(self, other) -> bool:
        return (
            self.cron_user == other.cron_user
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'cron_user': self.cron_user
        }


class Config:  # pylint: disable=too-many-instance-attributes
    """Configuration data."""
    log_dir: str
    homework_dir: str
    archive_dir: str
    db_path: str
    compose_file: str
    extra_compress_dirs: List[str]
    moodle_dl_dir: Optional[str]
    email: ConfigEmail
    home_assistant: Optional[ConfigHomeAssistant]
    portainer: Optional[ConfigPortainer]
    things_server: Optional[ConfigThingsServer]
    process: Optional[ConfigProcess]
    runner: Optional[ConfigRunner]

    # opress dangerous default values as that's only dangerous if they are modified
    def __init__(
        self,
        log_dir: str,
        homework_dir: str,
        archive_dir: str,
        db_path: str,
        compose_file: str,
        email: Dict[str, str],
        home_assistant: Dict[str, Any] = {
        },  # pylint: disable=dangerous-default-value
        portainer: Dict[str, Any] = {
        },  # pylint: disable=dangerous-default-value
        things_server: Dict[str, Any] = {
        },  # pylint: disable=dangerous-default-value
        process: Dict[str, str] = {
        },  # pylint: disable=dangerous-default-value
        runner: Dict[str, str] = {},  # pylint: disable=dangerous-default-value
        extra_compress_dirs: List[str] = [
        ],  # pylint: disable=dangerous-default-value
        moodle_dl_dir: Optional[str] = None
    ):  # pylint: disable=too-many-arguments
        self.log_dir = log_dir
        self.homework_dir = homework_dir
        self.archive_dir = archive_dir
        self.db_path = db_path
        self.compose_file = compose_file
        self.moodle_dl_dir = moodle_dl_dir
        self.extra_compress_dirs = extra_compress_dirs
        self.email = ConfigEmail(**email)
        self.home_assistant = ConfigHomeAssistant(home_assistant)
        self.portainer = ConfigPortainer(portainer)
        self.things_server = ConfigThingsServer(things_server)
        self.process = ConfigProcess(process)
        self.runner = ConfigRunner(runner)

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.log_dir == other.log_dir and
            self.homework_dir == other.homework_dir and
            self.archive_dir == other.archive_dir and
            self.db_path == other.db_path and
            self.compose_file == other.compose_file and
            self.moodle_dl_dir == other.moodle_dl_dir and
            self.email == other.email and
            self.home_assistant == other.home_assistant and
            self.portainer == other.portainer and
            self.things_server == other.things_server and
            self.process == other.process and
            self.runner == other.runner and
            self.extra_compress_dirs == other.extra_compress_dirs
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'log_dir': self.log_dir,
            'homework_dir': self.homework_dir,
            'archive_dir': self.archive_dir,
            'db_path': self.db_path,
            'compose_file': self.compose_file,
            'moodle_dl_dir': self.moodle_dl_dir,
            'email': self.email.to_dict() if self.email else None,
            'home_assistant': self.home_assistant.to_dict() if self.home_assistant else None,
            'portainer': self.portainer.to_dict() if self.portainer else None,
            'things_server': self.things_server.to_dict() if self.things_server else None,
            'process': self.process.to_dict() if self.process else None,
            'runner': self.runner.to_dict() if self.runner else None,
            'extra_compress_dirs': self.extra_compress_dirs
        }


class ConfigError(Exception):
    """An exception thrown when the config is oncomplete or invalid."""


def load_config(path: Optional[str] = None) -> Config:
    """Load config from file and return it."""
    if not path:
        path = "home_automation.conf.yml"
    with open(path, "r", encoding="utf-8") as file_obj:
        return parse_config(file_obj.read())


def parse_config(config: str) -> Config:
    """Parse config from string and return it."""
    data = yaml.safe_load(config)
    return Config(**data)
