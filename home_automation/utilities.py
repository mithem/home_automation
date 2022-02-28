"""Just some utilities, especially regarding mailing."""
import os
import pwd
import grp
import logging

import yagmail

import home_automation.config

home_automation.config.load_dotenv()

_EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", None)
if not _EMAIL_ADDRESS:
    raise Exception("Invalid $EMAIL_ADDRESS.")
_SMTP = yagmail.SMTP(_EMAIL_ADDRESS, os.environ.get("EMAIL_PASSWD"))


def send_mail(subject: str, body: str = ""):
    """Send mail now."""
    _SMTP.send(_EMAIL_ADDRESS, subject, body)


def check_for_root_privileges() -> bool:
    """Return whether this process is run by the root user."""
    return os.getuid() == 0


def drop_privileges(logger: logging.Logger = None):
    """Drop root privileges for those of the user & group
    specified in env-values `HOME_AUTOMATION_USER` & `HOME_AUTOMATION_GROUP`.

    Might throw:
    - OSError (error setting uid & gid)"""
    if logger:
        logger.info("Dropping privileges")
    if not check_for_root_privileges():
        return

    # to save errors occuring when setting uid/gid.
    # this way, each of those will be tried to set before escaping this function block
    # only the first error will actually be thrown, though
    errors = []

    target_username = os.environ.get("HOME_AUTOMATION_USER", None)
    target_group = os.environ.get("HOME_AUTOMATION_GROUP", None)

    current_uid = os.getuid()
    current_gid = os.getgid()
    username = pwd.getpwuid(current_uid).pw_name
    group = grp.getgrgid(current_gid).gr_name

    if target_username and username != target_username:
        target_uid = pwd.getpwnam(target_username).pw_uid
    else:
        target_uid = current_uid

    if target_group and group != target_group:
        target_gid = grp.getgrnam(target_group).gr_gid
    else:
        target_gid = current_gid

    try:
        os.setuid(target_uid)
    except OSError as err:
        errors.append(err)
    try:
        os.setgid(target_gid)
    except OSError as err:
        errors.append(err)

    usrstruct = pwd.getpwuid(os.getuid())
    groupstruct = grp.getgrgid(os.getgid())
    username = usrstruct.pw_name
    groupname = groupstruct.gr_name
    if logger:
        logger.info("Dropped privileges. Now running as %s / %s",
                    username, groupname)

    if errors:
        raise errors[0]


def check_current_user():
    """Return the current user & group."""
    uid = os.getuid()
    gid = os.getgid()

    user = pwd.getpwuid(uid).pw_name
    group = grp.getgrgid(gid).gr_name

    return (user, group)
