"""Everything to do with configuration."""
import os
from typing import Any, List, Dict, Optional, Union
import git
import yaml


class ConfigEmail:
    """Email configuration."""

    address: Optional[str]

    def __init__(self, data: Optional[Dict[str, str]] = None):
        if not data:
            self.address = None
            return
        address = data.get("address")
        self.address = address if isinstance(address, str) else None

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return self.address == other.address

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "address": self.address,
        }


class ConfigHomeAssistant:
    """Home Assistant configuration."""

    token: Optional[str]
    url: Optional[str]
    insecure_https: bool

    def __init__(self, data: Optional[Dict[str, Union[str, bool]]] = None):
        if not data:
            self.token = None
            self.url = None
            self.insecure_https = False
            return
        token = data.get("token")
        url = data.get("url")
        self.token = token if isinstance(token, str) else None
        self.url = url if isinstance(url, str) else None
        self.insecure_https = bool(data.get("insecure_https", False))

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.token == other.token
            and self.url == other.url
            and self.insecure_https == other.insecure_https
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "token": self.token,
            "insecure_https": self.insecure_https,
        }


class ConfigPortainer:
    """Portainer configuration."""

    url: Optional[str]
    username: Optional[str]
    password: Optional[str]
    home_assistant_env: Optional[str]
    home_assistant_stack: Optional[str]
    insecure_https: bool

    def __init__(self, data: Optional[Dict[str, Union[str, bool]]] = None):
        if not data:
            self.url = None
            self.username = None
            self.password = None
            self.home_assistant_env = None
            self.home_assistant_stack = None
            self.insecure_https = False
            return
        url = data.get("url")
        username = data.get("username")
        password = data.get("password")
        home_assistant_env = data.get("home_assistant_env")
        home_assistant_stack = data.get("home_assistant_stack")
        self.url = url if isinstance(url, str) else None
        self.username = username if isinstance(username, str) else None
        self.password = password if isinstance(password, str) else None
        self.home_assistant_env = (
            home_assistant_env if isinstance(home_assistant_env, str) else None
        )
        self.home_assistant_stack = (
            home_assistant_stack if isinstance(home_assistant_stack, str) else None
        )
        self.insecure_https = bool(data.get("insecure_https", False))

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.url == other.url
            and self.username == other.username
            and self.password == other.password
            and self.home_assistant_env == other.home_assistant_env
            and self.home_assistant_stack == other.home_assistant_stack
            and self.insecure_https == other.insecure_https
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "username": self.username,
            "password": self.password,
            "home_assistant_env": self.home_assistant_env,
            "home_assistant_stack": self.home_assistant_stack,
            "insecure_https": self.insecure_https,
        }

    def valid(self) -> bool:
        """Check if configuration is valid."""
        return (
            bool(self.url)
            and bool(self.username)
            and bool(self.password)
            and bool(self.home_assistant_env)
            and bool(self.home_assistant_stack)
        )


class ConfigThingsServer:
    """Things server configuration."""

    url: Optional[str]
    insecure_https: bool

    def __init__(self, data: Optional[Dict[str, Union[str, bool]]] = None):
        if not data:
            self.url = None
            self.insecure_https = False
            return
        url = data.get("url")
        self.url = url if isinstance(url, str) else None
        self.insecure_https = bool(data.get("insecure_https", False))

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return self.url == other.url and self.insecure_https == other.insecure_https

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"url": self.url, "insecure_https": self.insecure_https}


class ConfigProcess:
    """Configuration of the home_automation process."""

    user: Optional[str]
    group: Optional[str]

    def __init__(self, data: Optional[Dict[str, str]] = None):
        if not data:
            self.user = None
            self.group = None
            return
        self.user = data.get("user")
        self.group = data.get("group")

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return self.user == other.user and self.group == other.group

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"user": self.user, "group": self.group}


class ConfigRunner:  # pylint: disable=too-few-public-methods
    """home_automation.runner configuration."""

    cron_user: Optional[str]

    def __init__(self, data: Optional[Dict[str, str]] = None):
        if not data:
            self.cron_user = None
            return
        cron_user = data.get("cron_user")
        self.cron_user = cron_user

    def __eq__(self, other) -> bool:
        return self.cron_user == other.cron_user

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"cron_user": self.cron_user}


class ConfigKubernetes:
    """Kubernetes configuration."""

    url: Optional[str]
    insecure_https: bool
    ssl_ca_cert_path: Optional[str]
    api_key: Optional[str]
    namespace: Optional[str]
    deployment_name: Optional[str]

    def __init__(self, data: Optional[Dict[str, Union[str, bool]]] = None):
        if not data:
            self.url = None
            self.insecure_https = False
            self.ssl_ca_cert_path = None
            self.api_key = None
            self.namespace = None
            self.deployment_name = None
            return
        url = data.get("url")
        ssl_ca_cert_path = data.get("ssl_ca_cert_path", None)
        api_key = data.get("api_key")
        namespace = data.get("namespace")
        deployment_name = data.get("deployment_name")
        self.insecure_https = bool(data.get("insecure_https", False))
        self.url = url if isinstance(url, str) else None
        self.ssl_ca_cert_path = (
            ssl_ca_cert_path if isinstance(ssl_ca_cert_path, str) else None
        )
        self.api_key = api_key if isinstance(api_key, str) else None
        self.namespace = namespace if isinstance(namespace, str) else None
        self.deployment_name = (
            deployment_name if isinstance(deployment_name, str) else None
        )

    def __eq__(self, other) -> bool:
        return (
            self.url == other.url
            and self.insecure_https == other.insecure_https
            and self.ssl_ca_cert_path == other.ssl_ca_cert_path
            and self.api_key == other.api_key
            and self.namespace == other.namespace
            and self.deployment_name == other.deployment_name
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "insecure_https": self.insecure_https,
            "ssl_ca_cert_path": self.ssl_ca_cert_path,
            "api_key": self.api_key,
            "namespace": self.namespace,
            "deployment_name": self.deployment_name,
        }

    def valid(self) -> bool:
        """Check if configuration is valid."""
        return (
            bool(self.url)
            and bool(self.api_key)
            and bool(self.insecure_https)
            or bool(self.ssl_ca_cert_path)
        )


class ConfigAPIServer:
    """Configuration for the gunicorn server running the API."""

    interface: Optional[str]
    ssl_cert_path: Optional[str]
    ssl_key_path: Optional[str]
    workers: Optional[int]

    def __init__(self, data: Optional[Dict[str, str]] = None):
        if not data:
            self.interface = None
            self.ssl_cert_path = None
            self.ssl_key_path = None
            self.workers = None
            return
        interface = data.get("interface")
        ssl_cert_path = data.get("ssl_cert_path")
        ssl_key_path = data.get("ssl_key_path")
        workers = data.get("workers")
        self.interface = interface if isinstance(interface, str) else None
        self.ssl_cert_path = ssl_cert_path if isinstance(ssl_cert_path, str) else None
        self.ssl_key_path = ssl_key_path if isinstance(ssl_key_path, str) else None
        self.workers = workers if isinstance(workers, int) else None

    def __eq__(self, other) -> bool:
        return (
            self.interface == other.interface
            and self.ssl_cert_path == other.ssl_cert_path
            and self.ssl_key_path == other.ssl_key_path
            and self.workers == other.workers
        )

    def to_dict(self) -> Dict[str, Union[Optional[str], Optional[int]]]:
        """Convert to dictionary."""
        return {
            "interface": self.interface,
            "ssl_cert_path": self.ssl_cert_path,
            "ssl_key_path": self.ssl_key_path,
            "workers": self.workers,
        }

    def valid_ssl(self) -> bool:
        """Check if SSL configuration is valid."""
        return bool(self.ssl_cert_path) and bool(self.ssl_key_path)


class ConfigGit:
    """Configuration for the git repository."""

    remotes: List[str]
    branch: Optional[str]
    discard_changes: bool

    def __init__(self, data: Optional[Dict[str, Union[List[str], str, bool]]] = None):
        if not data:
            self.remotes = []
            self.branch = None
            self.discard_changes = False
            return
        remotes = data.get("remotes")
        branch = data.get("branch")
        discard_changes = data.get("discard_changes")
        self.remotes = (
            remotes
            if isinstance(remotes, list)
            else [remotes]
            if isinstance(remotes, str)
            else []
        )
        self.branch = branch if isinstance(branch, str) else None
        self.discard_changes = (
            discard_changes if isinstance(discard_changes, bool) else False
        )

    def __eq__(self, other) -> bool:
        return (
            self.remotes == other.remotes
            and self.branch == other.branch
            and self.discard_changes == other.discard_changes
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "remotes": self.remotes,
            "branch": self.branch,
            "discard_changes": self.discard_changes,
        }

    def valid(self) -> bool:
        """Check if configuration is valid."""
        remotes_valid = all(isinstance(x, str) for x in self.remotes)
        repo = git.Repo(os.curdir)
        branch_found = self.branch is None or self.branch in [
            branch.name for branch in repo.branches  # type: ignore
        ]
        return remotes_valid and branch_found


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
    home_assistant: ConfigHomeAssistant
    portainer: ConfigPortainer
    things_server: ConfigThingsServer
    process: ConfigProcess
    runner: ConfigRunner
    kubernetes: ConfigKubernetes
    api_server: ConfigAPIServer
    git: ConfigGit

    # opress dangerous default values as that"s only dangerous if they are modified
    def __init__(
        self,
        log_dir: str,
        homework_dir: str,
        archive_dir: str,
        db_path: str,
        compose_file: str,
        email: Dict[str, Any],
        home_assistant: Dict[str, Any] = None,
        portainer: Dict[str, Any] = None,
        things_server: Dict[str, Any] = None,
        process: Dict[str, str] = None,
        runner: Dict[str, str] = None,
        extra_compress_dirs: List[str] = None,
        moodle_dl_dir: Optional[str] = None,
        kubernetes: Dict[str, Union[str, bool]] = None,
        api_server: Dict[str, str] = None,
        git_data: Dict[str, Union[List[str], str, bool]] = None,
    ):  # pylint: disable=too-many-arguments,too-many-locals
        self.log_dir = log_dir
        self.homework_dir = homework_dir
        self.archive_dir = archive_dir
        self.db_path = db_path
        self.compose_file = compose_file
        self.moodle_dl_dir = moodle_dl_dir
        self.extra_compress_dirs = extra_compress_dirs if extra_compress_dirs else []
        self.email = ConfigEmail(email)
        self.home_assistant = ConfigHomeAssistant(home_assistant)
        self.portainer = ConfigPortainer(portainer)
        self.things_server = ConfigThingsServer(things_server)
        self.process = ConfigProcess(process)
        self.runner = ConfigRunner(runner)
        self.kubernetes = ConfigKubernetes(kubernetes)
        self.api_server = ConfigAPIServer(api_server)
        self.git = ConfigGit(git_data)

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.log_dir == other.log_dir
            and self.homework_dir == other.homework_dir
            and self.archive_dir == other.archive_dir
            and self.db_path == other.db_path
            and self.compose_file == other.compose_file
            and self.moodle_dl_dir == other.moodle_dl_dir
            and self.email == other.email
            and self.home_assistant == other.home_assistant
            and self.portainer == other.portainer
            and self.things_server == other.things_server
            and self.process == other.process
            and self.runner == other.runner
            and self.extra_compress_dirs == other.extra_compress_dirs
            and self.kubernetes == other.kubernetes
            and self.api_server == other.api_server
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "log_dir": self.log_dir,
            "homework_dir": self.homework_dir,
            "archive_dir": self.archive_dir,
            "db_path": self.db_path,
            "compose_file": self.compose_file,
            "moodle_dl_dir": self.moodle_dl_dir,
            "email": self.email.to_dict() if self.email else None,
            "home_assistant": self.home_assistant.to_dict()
            if self.home_assistant
            else None,
            "portainer": self.portainer.to_dict() if self.portainer else None,
            "things_server": self.things_server.to_dict()
            if self.things_server
            else None,
            "process": self.process.to_dict() if self.process else None,
            "runner": self.runner.to_dict() if self.runner else None,
            "extra_compress_dirs": self.extra_compress_dirs,
            "kubernetes": self.kubernetes.to_dict() if self.kubernetes else None,
            "api_server": self.api_server.to_dict() if self.api_server else None,
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
