# just need to implement this by myself as dotenv isn't easily available on Synology DSM.
import os


def load_dotenv():
    def load(s: str):
        with open(s, "r") as f:
            lines = f.readlines()
        for line in lines:
            varname, value = line.split("=")
            os.environ[varname] = value.replace("\n", "")
    try:
        load(".env")
    except FileNotFoundError:
        load("/volume2/repos/home-automation/.env")
