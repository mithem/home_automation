import os


def load_dotenv():
    with open(".env", "r") as f:
        lines = f.readlines()
    for line in lines:
        varname, value = line.split("=")
        os.environ[varname] = value.replace("\n", "")
