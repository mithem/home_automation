from setuptools import setup


packages = ["home_automation"]

requirements = [
    "argparse",
    "flask",
    "yagmail",
    "argparse",
    "fileloghelper",
    "httpx",
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
    "tox"
]

with open("requirements_dev.txt", "w") as f:
    f.writelines([r + "\n" for r in requirements])

setup(
    name="home_automation",
    version="1.0.0",
    packages=packages,
    install_requires=requirements
)
