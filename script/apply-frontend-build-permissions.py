#!/usr/bin/python3
# pylint: disable=invalid-name
"""Apply permissions for frontend build."""
import os


def apply_permissions(path: str):
    """Apply permissions to dir at `path`"""
    if not os.path.isdir(path):
        raise Exception(f"Not a dir: '{path}'")
    for root, dirs, files in os.walk(path):
        for fname in files:
            path = os.path.join(root, fname)
            os.chown(path, 33, 33)  # what nginx container has for www-data
            os.chmod(path, 0o644)
        for dirname in dirs:
            path = os.path.join(root, dirname)
            os.chown(path, 33, 33)  # what nginx container has for www-data
            os.chmod(path, 0o755)


PATH_PROGRESSION = "home_automation/server/frontend/build"
progression_root = f"./{PATH_PROGRESSION}"

try:
    apply_permissions(progression_root)
except Exception as e:  # pylint: disable=broad-except
    print(e)
    progression_root = f"../{PATH_PROGRESSION}"
    try:
        apply_permissions(progression_root)
    except Exception as e:  # pylint: disable=broad-except
        print(e)
