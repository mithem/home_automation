import os
from setuptools import setup
import re
import home_automation

VERSION = "1.1.0-b9"

with open("home_automation/__init__.py", "r") as f:
    code = f.read()

code = code.replace(home_automation.VERSION, VERSION, 1)

with open("home_automation/__init__.py", "w") as f:
    f.write(code)

packages = ["home_automation", "home_automation.server.backend"]

requirements = [
    "argparse",
    "flask[async]",
    "yagmail",
    "fileloghelper",
    "httpx>=0.18,<0.21",
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
    "moodle-dl"
]

with open("requirements_dev.txt", "w") as f:
    f.writelines([r + "\n" for r in requirements])

setup(
    name="home_automation",
    version=VERSION,
    packages=packages,
    install_requires=requirements
)
