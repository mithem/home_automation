"""Just some utilities, especially regarding mailing."""
import argparse
import base64
import grp
import logging
import os
import pwd
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from kubernetes import client as klient

from home_automation import config as haconfig


def send_mail(
    config: haconfig.Config, credentials: Credentials, subject: str, body: str = ""
):
    """Send mail now."""
    gmail = build("gmail", "v1", credentials=credentials)
    message = MIMEText(body)
    message["To"] = config.email.address
    message["From"] = config.email.address
    message["Subject"] = subject
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
    payload = {"raw": encoded}
    gmail.users().messages().send(  # pylint: disable=no-member
        userId="me", body=payload
    ).execute()


def check_for_root_privileges() -> bool:
    """Return whether this process is run by the root user."""
    return os.getuid() == 0


def drop_privileges(config: haconfig.Config, logger: logging.Logger = None):
    """Drop root privileges for those of the user & group
    specified in env-values `HOME_AUTOMATION_USER` & `HOME_AUTOMATION_GROUP`.

    Might throw:
    - OSError (error setting uid & gid)"""
    if logger:
        logger.info("Dropping privileges")
    if not config.process:
        return
    if not check_for_root_privileges():
        return

    # to save errors occuring when setting uid/gid.
    # this way, each of those will be tried to set before escaping this function block
    # only the first error will actually be thrown, though
    errors = []

    target_username = config.process.user
    target_group = config.process.group

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
        # first set group, then user as doing otherwise
        # doesn't permit new non-root user to set group
        os.setgid(target_gid)
    except OSError as err:
        errors.append(err)
    try:
        os.setuid(target_uid)
    except OSError as err:
        errors.append(err)

    usrstruct = pwd.getpwuid(os.getuid())
    groupstruct = grp.getgrgid(os.getgid())
    username = usrstruct.pw_name
    groupname = groupstruct.gr_name
    if logger:
        logger.info("Dropped privileges. Now running as %s / %s", username, groupname)

    if errors:
        raise errors[0]


def check_current_user():
    """Return the current user & group."""
    uid = os.getuid()
    gid = os.getgid()

    user = pwd.getpwuid(uid).pw_name
    group = grp.getgrgid(gid).gr_name

    return (user, group)


def get_k8s_client(config: haconfig.Config) -> klient.ApiClient:
    """Return the k8s client using the specified config."""
    assert config.kubernetes, "No kubernetes config found."
    konfig = klient.Configuration()
    konfig.host = config.kubernetes.url
    konfig.verify_ssl = not config.kubernetes.insecure_https
    konfig.api_key = {"authorization": f"Bearer {config.kubernetes.api_key}"}
    return klient.ApiClient(konfig)


def argparse_add_argument_for_config_file_path(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Add an argument for the config file path to the specified parser. (args.config is set to the path to config file)"""
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="/etc/home_automation/config.yaml",
        help="Path to the config file.",
    )
    return parser
