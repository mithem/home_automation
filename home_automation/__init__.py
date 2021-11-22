"""A project for home automation. That's organizing and compressing homework on
truenas and related scripts/programs or otherwise useful but maybe unrelated stuff."""
import os

import yagmail

import home_automation.config

VERSION="1.1.0-b10"

home_automation.config.load_dotenv()

_EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
_SMTP = yagmail.SMTP(_EMAIL_ADDRESS, os.environ.get("EMAIL_PASSWD"))

def send_mail(subject: str, body: str = ""):
    _SMTP.send(_EMAIL_ADDRESS, subject, body)

