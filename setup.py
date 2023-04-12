from setuptools import setup

VERSION = "2.6.0-b8"

try:
    import home_automation

    with open("home_automation/__init__.py", "r", encoding="utf-8") as f:
        code = f.read()

    code = code.replace(home_automation.VERSION, VERSION, 1)

    with open("home_automation/__init__.py", "w", encoding="utf-8") as f:
        f.write(code)
except ImportError:
    pass


with open("VERSION", "w", encoding="utf-8") as f:
    f.write(VERSION)

packages = ["home_automation"]


requirements = [
    "argparse",
    "flask[async]",
    "fileloghelper",
    "httpx>=0.18,<0.25",
    "pytest",
    "pytest-cov",
    "pytest-asyncio",
    "pytest-httpx",
    "pytest-flask",
    "pyfakefs",
    "pylint",
    "pylint-exit",
    "aiohttp",
    "mypy",
    "mypy-extensions",
    "types-requests",
    "tox==4.*",
    "python-crontab",
    "croniter",
    "watchdog",
    "pid",
    "docker",
    "gunicorn",
    "requests",
    "semver",
    "GitPython",
    "moodle-dl",
    "pyyaml",
    "kubernetes",
    "google-api-python-client",
    "google-auth",
    "google-auth-oauthlib",
    "google-auth-httplib2",
    "setproctitle",
    "redis",
]

with open("requirements.txt", "w") as f:
    f.writelines([r + "\n" for r in requirements])

setup(
    name="home_automation",
    version=VERSION,
    packages=packages,
    install_requires=requirements,
)
