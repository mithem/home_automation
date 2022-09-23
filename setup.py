from setuptools import setup
import home_automation

VERSION = "2.4.1-b2"

with open("home_automation/__init__.py", "r") as f:
    code = f.read()

code = code.replace(home_automation.VERSION, VERSION, 1)

with open("home_automation/__init__.py", "w") as f:
    f.write(code)

with open("VERSION", "w") as f:
    f.write(VERSION)

packages = ["home_automation"]


requirements = [
    "argparse",
    "flask[async]",
    "fileloghelper",
    "httpx>=0.18,<0.24",
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
    "tox==3.*",
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
