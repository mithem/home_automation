"""Schedule appropriate cron jobs and run them (blocks permanently)"""
import os
from crontab import CronTab
from fileloghelper import Logger

from home_automation.config import load_dotenv

load_dotenv()

CRONTAB_FILE_NAME = "home_automation.tab"
LOG_DIR = os.environ.get("LOG_DIR", os.curdir)
HOMEWORK_DIR = os.environ.get("HOMEWORK_DIR")
ARCHIVE_DIR = os.environ.get("ARCHIVE_DIR")
logger = Logger(os.path.join(LOG_DIR, "home_automation_cron.log"),
                "home_automation_cron", autosave=True)


def setup():
    """Set up local filesystem for home_automation (create necessary dirs)."""
    os.makedirs(HOMEWORK_DIR)
    os.makedirs(ARCHIVE_DIR)


def main(cron_user: str = None):
    """Schedule appropriate cron jobs and run them (blocks permanently)"""
    if not cron_user:
        cron_user = os.environ.get("CRON_USER")

    def load_crontab():
        cron = CronTab(user=cron_user, tabfile=CRONTAB_FILE_NAME)
        return cron

    try:
        cron = load_crontab()
    except FileNotFoundError:
        with open(CRONTAB_FILE_NAME, "w"):
            pass
        cron = load_crontab()

    cron.remove_all()

    archiving_job = cron.new(
        command="python3 -m home_automation.archive_manager archive")
    reorganization_job = cron.new(
        command="python3 -m home_automation.archive_manager reorganize")
    compression_watcher_job = cron.new(
        command=f"python3 -m watch_fs -d '{HOMEWORK_DIR}' \
                'python3 -m home_automation.compression_manager'")

    archiving_job.minute.on(0)
    archiving_job.hour.on(0)
    archiving_job.dow.on("SAT")

    reorganization_job.minute.on(0)
    reorganization_job.hour.on(0)
    reorganization_job.day.on(1)

    compression_watcher_job.every_reboot()

    cron.write()  # not sure if I could run the scheduler without writing the file

    logger.info("Running cron jobs until interrupted...", True)
    try:
        for result in cron.run_scheduler():
            logger.info(f"Ran cron job. Ouput: {result}")
    except KeyboardInterrupt:
        logger.info(
            "Stopped cron scheduler. home_automation will not run future jobs.", True)


if __name__ == "__main__":
    setup()
    main()
