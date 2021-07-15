from setuptools import setup


packages = ["Home_Automation"]

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
    "pyfakefs"
]

with open("requirements_dev.txt", "w") as f:
    f.writelines([r + "\n" for r in requirements])

setup(
    name="Home-Automation",
    version="1.0.0",
    packages=packages,
    install_requires=requirements
)
