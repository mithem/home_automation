import os
from setuptools import setup
import re

VERSION = "1.0.0"

with open("home_automation/__init__.py", "r") as f:
    code = "\n".join(f.readlines())

code = re.sub(r"""VERSION ?= ?("|')\d+\.\d+\.\d+("|')""", "VERSION = \"" + VERSION + "\"", code)

with open("home_automation/__init__.py", "w") as f:
    f.flush()
    f.writelines(code.split("\n"))

packages = ["home_automation", "home_automation.server.backend"]

requirements = [
    "argparse",
    "flask[async]",
    "yagmail",
    "fileloghelper",
    "httpx>=0.18,<0.20",
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
    "tox==3.*",
    "python-crontab",
    "croniter",
    "watchdog",
    "pid",
    "docker",
    "gunicorn"
]

with open("requirements_dev.txt", "w") as f:
    f.writelines([r + "\n" for r in requirements])

setup(
    name="home_automation",
    version=VERSION,
    packages=packages,
    install_requires=requirements
)
