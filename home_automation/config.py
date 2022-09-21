"""Everything to do with configuration."""
# pylint: disable=too-many-lines
import os
import pwd
import socket as socketlib
from typing import Any, Dict, List, Optional, Union

import git as gitlib
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

    class ConfigHomeAssistantK8sDeployment:
        """The k8s deployment of Home Assistant."""

        namespace: Optional[str]
        name: str

        def __init__(self, data: Dict[str, Optional[str]]):
            namespace = data.get("namespace")
            name = data["name"]
            self.namespace = namespace if isinstance(namespace, str) else None
            if isinstance(name, str):
                self.name = name
            else:
                raise ValueError("Missing home_assistant.deployment.name")

        def __eq__(self, other) -> bool:
            return self.namespace == other.namespace and self.name == other.name

        def to_dict(self) -> Dict[str, Optional[str]]:
            """Convert to dictionary."""
            return {
                "namespace": self.namespace,
                "name": self.name,
            }

    class ConfigHomeAssistantPortainer:
        """The portainer information for Home Assistant."""

        environment: str
        stack: str

        def __init__(self, data: Dict[str, Optional[str]]):
            environment = data["environment"]
            stack = data["stack"]
            if environment:
                self.environment = environment
            else:
                raise ConfigError("Missing home_assistant.portainer.environment")
            if stack:
                self.stack = stack
            else:
                raise ConfigError("Missing home_assistant.portainer.stack")

        def __eq__(self, other) -> bool:
            return self.environment == other.environment and self.stack == other.stack

        def to_dict(self) -> Dict[str, Optional[str]]:
            """Convert to dictionary."""
            return {
                "environment": self.environment,
                "stack": self.stack,
            }

    token: Optional[str]
    url: Optional[str]
    insecure_https: bool
    deployment: Optional[ConfigHomeAssistantK8sDeployment]
    portainer: Optional[ConfigHomeAssistantPortainer]

    def __init__(
        self,
        data: Optional[Dict[str, Union[str, bool, Dict[str, Optional[str]]]]] = None,
    ):
        if not data:
            self.token = None
            self.url = None
            self.insecure_https = False
            self.deployment = None
            self.portainer = None
            return
        token = data.get("token")
        url = data.get("url")
        deployment = data.get("deployment")
        portainer = data.get("portainer")
        self.token = token if isinstance(token, str) else None
        self.url = url if isinstance(url, str) else None
        self.insecure_https = bool(data.get("insecure_https", False))
        if isinstance(deployment, dict):
            self.deployment = ConfigHomeAssistant.ConfigHomeAssistantK8sDeployment(
                deployment
            )
        else:
            self.deployment = None
        if isinstance(portainer, dict):
            self.portainer = ConfigHomeAssistant.ConfigHomeAssistantPortainer(portainer)
        else:
            self.portainer = None

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.token == other.token
            and self.url == other.url
            and self.insecure_https == other.insecure_https
            and self.deployment == other.deployment
            and self.portainer == other.portainer
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "token": self.token,
            "insecure_https": self.insecure_https,
            "deployment": self.deployment,
            "portainer": self.portainer,
        }


class ConfigPortainer:
    """Portainer configuration."""

    url: Optional[str]
    username: Optional[str]
    password: Optional[str]
    insecure_https: bool

    def __init__(self, data: Optional[Dict[str, Union[str, bool]]] = None):
        if not data:
            self.url = None
            self.username = None
            self.password = None
            self.insecure_https = False
            return
        url = data.get("url")
        username = data.get("username")
        password = data.get("password")
        self.url = url if isinstance(url, str) else None
        self.username = username if isinstance(username, str) else None
        self.password = password if isinstance(password, str) else None
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
            and self.insecure_https == other.insecure_https
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "username": self.username,
            "password": self.password,
            "insecure_https": self.insecure_https,
        }

    def valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.url) and bool(self.username) and bool(self.password)


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

    def __init__(self, data: Optional[Dict[str, Union[str, bool]]] = None):
        if not data:
            self.url = None
            self.insecure_https = False
            self.ssl_ca_cert_path = None
            self.api_key = None
            return
        url = data.get("url")
        ssl_ca_cert_path = data.get("ssl_ca_cert_path", None)
        api_key = data.get("api_key")
        self.insecure_https = bool(data.get("insecure_https", False))
        self.url = url if isinstance(url, str) else None
        self.ssl_ca_cert_path = (
            ssl_ca_cert_path if isinstance(ssl_ca_cert_path, str) else None
        )
        self.api_key = api_key if isinstance(api_key, str) else None

    def __eq__(self, other) -> bool:
        return (
            self.url == other.url
            and self.insecure_https == other.insecure_https
            and self.ssl_ca_cert_path == other.ssl_ca_cert_path
            and self.api_key == other.api_key
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "insecure_https": self.insecure_https,
            "ssl_ca_cert_path": self.ssl_ca_cert_path,
            "api_key": self.api_key,
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
        repo = gitlib.Repo(os.curdir)
        branch_found = self.branch is None or self.branch in [
            branch.name for branch in repo.branches  # type: ignore
        ]
        return remotes_valid and branch_found


class ConfigFrontend:
    """Configuration for the frontend."""

    image_name: str
    replicas: int
    deployment_name: str
    namespace: str
    service_name: str
    backend_ip_address: str

    def __init__(
        self, data: Optional[Dict[str, Union[str, int]]] = None
    ):  # pylint: disable=too-many-branches
        if not data:
            self.image_name = "home_automation_frontend"
            self.replicas = 1
            self.deployment_name = "frontend"
            self.namespace = "default"
            self.service_name = "frontend"
            self.backend_ip_address = socketlib.gethostbyname(socketlib.gethostname())
            return
        image_name = data.get("image_name")
        deployment_name = data.get("deployment_name")
        namespace = data.get("namespace")
        replicas = data.get("replicas")
        service_name = data.get("service_name")
        backend_ip_address = data.get("backend_ip_address")
        if isinstance(image_name, str):
            self.image_name = image_name
        else:
            self.image_name = "home_automation_frontend"
        if isinstance(deployment_name, str):
            self.deployment_name = deployment_name
        else:
            self.deployment_name = "frontend"
        if isinstance(namespace, str):
            self.namespace = namespace
        else:
            self.namespace = "default"
        if isinstance(replicas, int):
            self.replicas = replicas
        else:
            self.replicas = 1
        if isinstance(service_name, str):
            self.service_name = service_name
        else:
            self.service_name = "frontend"
        if isinstance(backend_ip_address, str):
            self.backend_ip_address = backend_ip_address
        else:
            self.backend_ip_address = socketlib.gethostbyname(socketlib.gethostname())

    def __eq__(self, other) -> bool:
        return (
            self.image_name == other.image_name
            and self.replicas == other.replicas
            and self.deployment_name == other.deployment_name
            and self.namespace == other.namespace
            and self.service_name == other.service_name
            and self.backend_ip_address == other.backend_ip_address
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "image_name": self.image_name,
            "replicas": self.replicas,
            "deployment_name": self.deployment_name,
            "namespace": self.namespace,
            "service_name": self.service_name,
            "backend_ip_address": self.backend_ip_address,
        }

    def valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.image_name)


class ConfigDocker:
    """Docker configuration."""

    class ConfigDockerRegistry:
        """Docker registry configuration"""

        class ConfigDockerRegistryAuth:
            """Authentication configuration for docker registry."""

            username: str
            password: str

            def __init__(self, data: Dict[str, str]):
                self.username = data["username"]
                self.password = data["password"]

            def __eq__(self, other) -> bool:
                return (
                    self.username == other.username and self.password == other.password
                )

            def to_dict(self) -> Dict[str, str]:
                """Convert to dictionary."""
                return {
                    "username": self.username,
                    "password": self.password,
                }

        auth: Optional[ConfigDockerRegistryAuth]
        registry_url: str

        def __init__(self, data: Dict[str, Union[Dict, str]]):
            auth = data.get("auth")
            registry_url = data["registry_url"]
            if isinstance(auth, dict):
                self.auth = ConfigDocker.ConfigDockerRegistry.ConfigDockerRegistryAuth(
                    auth
                )
            else:
                self.auth = None
            if isinstance(registry_url, str):
                self.registry_url = registry_url
            else:
                raise ValueError(
                    f"Unexpected value '{registry_url}' for docker.registry.registry_url."
                )

        def __eq__(self, other) -> bool:
            return self.auth == other.auth and self.registry_url == other.registry_url

        def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary."""
            return {
                "registry_url": self.registry_url,
                "auth": self.auth.to_dict() if self.auth else None,
            }

    class ConfigDockerBuildConfig:
        """Configuration for how docker builds images."""

        network: Optional[str]
        no_cache: bool

        def __init__(self, data: Dict[str, Union[str, bool]]):
            network = data.get("network")
            no_cache = data.get("no_cache")
            if isinstance(network, str):
                self.network = network
            else:
                self.network = None
            if isinstance(no_cache, bool):
                self.no_cache = no_cache
            else:
                self.no_cache = False

        def __eq__(self, other) -> bool:
            return self.network == other.network and self.no_cache == other.no_cache

        def to_dict(self) -> Dict[str, Union[Optional[str], bool]]:
            """Convert to dictionary."""
            return {
                "network": self.network,
                "no_cache": self.no_cache,
            }

    registry: Optional[ConfigDockerRegistry]
    build: ConfigDockerBuildConfig

    def __init__(self, data: Optional[Dict[str, Dict]] = None):
        if not data:
            self.registry = None
            self.build = ConfigDocker.ConfigDockerBuildConfig({})
            return
        registry = data.get("registry")
        if registry:
            self.registry = ConfigDocker.ConfigDockerRegistry(registry)
        else:
            self.registry = None
        self.build = ConfigDocker.ConfigDockerBuildConfig(data.get("build", {}))

    def __eq__(self, other) -> bool:
        return self.registry == other.registry and self.build == other.build

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "registry": self.registry.to_dict() if self.registry else None,
            "build": self.build.to_dict() if self.build else None,
        }


class ConfigHeimdall:
    """Heimdall configuration"""

    url: Optional[str]

    def __init__(self, data: Optional[Dict[str, Optional[str]]] = None):
        if not data:
            self.url = None
            return
        self.url = data.get("url")

    def __eq__(self, other) -> bool:
        return self.url == other.url

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary."""
        return {"url": self.url}


class ConfigStorageSQLite:
    """SQLite storage configuration."""

    path: str

    def __init__(self, data: Optional[Dict[str, str]] = None):
        if not data:
            self.path = "home_automation_backend.db"
            return
        self.path = data["path"]

    def __eq__(self, other) -> bool:
        return self.path == other.path

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {"path": self.path}

    def valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.path)


class ConfigStorageRedis:
    """Redis storage configuration."""

    host: str
    port: int
    user: Optional[str]
    password: Optional[str]

    def __init__(self, data: Dict[str, Union[str, int]]):
        assert isinstance(data["host"], str)
        assert isinstance(data["port"], int)
        user = data.get("user")
        password = data.get("password")
        if isinstance(user, str):
            self.user = user
        else:
            self.user = None
        if isinstance(password, str):
            self.password = password
        else:
            self.password = None
        self.host = data["host"]
        self.port = data["port"]

    def __eq__(self, other) -> bool:
        return (
            self.host == other.host
            and self.port == other.port
            and self.user == other.user
            and self.password == other.password
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
        }

    def valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.host) and bool(self.port)


class ConfigStorage:
    """Storage configuration"""

    file: Optional[ConfigStorageSQLite]
    redis: Optional[ConfigStorageRedis]

    def __init__(self, data: Optional[Dict[str, Dict]] = None):
        if not data:
            self.file = ConfigStorageSQLite()
            self.redis = None
            return
        file = data.get("file")
        if file:
            self.file = ConfigStorageSQLite(file)
        else:
            self.file = None
        redis = data.get("redis")
        if redis:
            self.redis = ConfigStorageRedis(redis)
        else:
            self.redis = None

    def __eq__(self, other) -> bool:
        return self.file == other.file and self.redis == other.redis

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file": self.file.to_dict() if self.file else None,
            "redis": self.redis.to_dict() if self.redis else None,
        }

    def valid(self) -> bool:
        """Check if configuration is valid."""
        if self.redis:
            return self.redis.valid()
        if self.file:
            return self.file.valid()
        return False

    def use_redis(self) -> bool:
        """Check if redis is used."""
        if self.redis:
            return self.redis.valid()
        return False


class ConfigAdminPermissions:
    """Admin permissions configuration."""

    user: Optional[str]
    password: Optional[str]

    def __init__(self, data: Dict[Optional[str], Optional[str]] = None):
        if data:
            self.user = data.get("user")
            self.password = data.get("password")
        else:
            self.user = None
            self.password = None

    def __eq__(self, other) -> bool:
        return self.user == other.user and self.password == other.password

    def to_dict(self) -> Dict[Optional[str], Optional[str]]:
        """Convert to dictionary."""
        return {"user": self.user, "password": self.password}

    def __str__(self):
        return f"AdminPermissions(user='{self.user}', password=******)"


class ConfigMiddlewareLaTeXToPDFMiddleware:
    """Configuration for the LaTeXToPDFMiddleware."""

    delete_log_file: bool
    delete_aux_file: bool
    delete_dvi_file: bool

    def __init__(self, data: Optional[Dict[str, bool]] = None):
        if not data:
            self.delete_log_file = False
            self.delete_aux_file = False
            self.delete_dvi_file = False
            return
        self.delete_log_file = data.get("delete_log_file", False)
        self.delete_aux_file = data.get("delete_aux_file", False)
        self.delete_dvi_file = data.get("delete_dvi_file", False)

    def __eq__(self, other) -> bool:
        if not other:
            return False
        return (
            self.delete_log_file == other.delete_log_file
            and self.delete_aux_file == other.delete_aux_file
            and self.delete_dvi_file == other.delete_dvi_file
        )

    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary."""
        return {
            "delete_log_file": self.delete_log_file,
            "delete_aux_file": self.delete_aux_file,
            "delete_dvi_file": self.delete_dvi_file,
        }


class ConfigMiddleware:
    """Middleware configuration."""

    latex_to_pdf: Optional[ConfigMiddlewareLaTeXToPDFMiddleware]

    def __init__(self, data: Optional[Dict[str, Dict]] = None):
        if data:
            self.latex_to_pdf = ConfigMiddlewareLaTeXToPDFMiddleware(
                data.get("latex_to_pdf")
            )
        else:
            self.latex_to_pdf = None

    def __eq__(self, other) -> bool:
        return self.latex_to_pdf == other.latex_to_pdf

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "latex_to_pdf": self.latex_to_pdf.to_dict() if self.latex_to_pdf else None,
        }


class Config:  # pylint: disable=too-many-instance-attributes
    """Configuration data."""

    log_dir: str
    homework_dir: str
    archive_dir: str
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
    frontend: ConfigFrontend
    docker: ConfigDocker
    heimdall: ConfigHeimdall
    storage: ConfigStorage
    admin: ConfigAdminPermissions
    middleware: ConfigMiddleware

    # opress dangerous default values as that's only dangerous if they are modified
    def __init__(
        self,
        log_dir: str,
        homework_dir: str,
        archive_dir: str,
        email: Dict[str, Any],
        compose_file: str = None,
        home_assistant: Dict[str, Any] = None,
        portainer: Dict[str, Any] = None,
        things_server: Dict[str, Any] = None,
        process: Dict[str, str] = None,
        runner: Dict[str, str] = None,
        extra_compress_dirs: List[str] = None,
        moodle_dl_dir: Optional[str] = None,
        kubernetes: Dict[str, Union[str, bool]] = None,
        api_server: Dict[str, str] = None,
        git: Dict[str, Union[List[str], str, bool]] = None,
        frontend: Dict[str, Union[str, int]] = None,
        docker: Dict[str, Dict] = None,
        heimdall: Dict[str, Optional[str]] = None,
        storage: Dict[str, Dict] = None,
        admin: Dict[Optional[str], Optional[str]] = None,
        middleware: Dict[str, Dict] = None,
    ):  # pylint: disable=too-many-arguments,too-many-locals
        self.log_dir = log_dir
        self.homework_dir = homework_dir
        self.archive_dir = archive_dir
        self.compose_file = compose_file if compose_file else "docker-compose.yml"
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
        self.git = ConfigGit(git)
        self.frontend = ConfigFrontend(frontend)
        self.docker = ConfigDocker(docker)
        self.heimdall = ConfigHeimdall(heimdall)
        self.storage = ConfigStorage(storage)
        self.admin = ConfigAdminPermissions(admin)
        self.middleware = ConfigMiddleware(middleware)

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.log_dir == other.log_dir
            and self.homework_dir == other.homework_dir
            and self.archive_dir == other.archive_dir
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
            and self.git == other.git
            and self.frontend == other.frontend
            and self.docker == other.docker
            and self.heimdall == other.heimdall
            and self.storage == other.storage
            and self.admin == other.admin
            and self.middleware == other.middleware
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "log_dir": self.log_dir,
            "homework_dir": self.homework_dir,
            "archive_dir": self.archive_dir,
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
            "git": self.git.to_dict() if self.git else None,
            "frontend": self.frontend.to_dict() if self.frontend else None,
            "docker": self.docker.to_dict() if self.docker else None,
            "heimdall": self.heimdall.to_dict() if self.heimdall else None,
            "storage": self.storage.to_dict() if self.storage else None,
            "admin": self.admin.to_dict() if self.admin else None,
            "middleware": self.middleware.to_dict() if self.middleware else None,
        }


class ConfigError(Exception):
    """An exception thrown when the config is oncomplete or invalid."""


def load_config(path: Optional[str] = None) -> Config:
    """Load config from file and return it."""
    if not path:
        path = "home_automation.conf.yml"
    with open(path, "r", encoding="utf-8") as file_obj:
        config = parse_config(file_obj.read())
        apply_config_file_permissions(path, config)
        return config


def apply_config_file_permissions(path: str, config: Config) -> None:
    """Apply the config file permissions in order to not leak the root password."""
    if config.admin:
        if config.admin.user:
            gid = pwd.getpwnam(config.admin.user).pw_gid
            execute_privileged_shell_command(
                config, f"chown '{config.admin.user}':'{gid}' '{path}'"
            )
            execute_privileged_shell_command(config, f"sudo -Sp '' chmod 110 '{path}'")


def parse_config(config: str) -> Config:
    """Parse config from string and return it."""
    data = yaml.safe_load(config)
    return Config(**data)


# not really appropriate here, but there's a circular import
# when putting it in either utilities or home_automation(.__init__)
def execute_privileged_shell_command(config: Config, command: str):
    """Execute the specified command as root."""
    os.system(f"echo '{config.admin.password}' | sudo -Sp '' {command}")
