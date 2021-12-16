#!/usr/bin/python3
import os

def apply_permissions(path: str):
    if not os.path.isdir(path):
        raise Exception(f"Not a dir: '{path}'")
    for root, dirs, files in os.walk("."):
        for fname in files:
            path = os.path.join(root, fname)
            os.chmod(path, 0o644)
        for dirname in dirs:
            path = os.path.join(root, dirname)
            os.chmod(path, 0o755)

path_progression = "home_automation/server/frontend/build"
root = f"./{path_progression}"

try:
    apply_permissions(root)
except Exception as e:
    print(e)
    root = f"../{path_progression}"
    try:
        apply_permissions(root)
    except Exception as e:
        print(e)
