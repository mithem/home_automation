import os
from setuptools import setup

VERSION = "1.0.0"

packages = ["home_automation", "home_automation.server.backend"]

requirements = [
    "argparse",
    "flask",
    "yagmail",
    "argparse",
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
    "docker"
]

with open("requirements_dev.txt", "w") as f:
    f.writelines([r + "\n" for r in requirements])

setup(
    name="home_automation",
    version=VERSION,
    packages=packages,
    install_requires=requirements
)
