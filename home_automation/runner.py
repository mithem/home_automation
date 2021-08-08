"""Schedule appropriate cron jobs and run them (blocks permanently)"""
import os
import time
import multiprocessing as mp
import signal
from pid.decorator import pidfile

from crontab import CronTab
from fileloghelper import Logger
from watchdog.observers import Observer as WatchdogObserver

from home_automation.config import load_dotenv

load_dotenv()

CRONTAB_FILE_NAME = "home_automation.tab"
LOG_DIR = os.environ.get("LOG_DIR", os.curdir)
HOMEWORK_DIR = os.environ.get("HOMEWORK_DIR")
ARCHIVE_DIR = os.environ.get("ARCHIVE_DIR")
PID_FILE_NAME = "home_automation.runner"
TERM_SWITCH = False
logger = Logger(os.path.join(LOG_DIR, "home_automation_runner.log"),
                "runner", autosave=True)


class LockError(Exception):
    """An error representing an anomaly handling the lock."""


class ProcessExit(Exception):
    """An error indicating the process should stop when thrown."""


def signal_handler(num, frame):  # pylint: disable=unused-argument
    """Respond to signal. Supports: SIGINT, SIGTERM."""
    supported = [signal.SIGINT, signal.SIGTERM]
    if num in supported:
        raise ProcessExit()


def setup():
    """Set up local filesystem for home_automation (create necessary dirs)
    and register signal handler."""
    for path in [HOMEWORK_DIR, ARCHIVE_DIR]:
        try:
            os.makedirs(path)
        except FileExistsError:
            continue
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def run_cron_jobs(cron_user: str = None):
    """Schedule cron jobs and run them."""
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

    logger.context = "runner.cron"
    logger.info("Running cron jobs until interrupted...", True)
    try:
        for result in cron.run_scheduler():
            logger.context = "runner.cron"
            logger.info(f"Ran cron job. Ouput: {result}")
    except ProcessExit:
        logger.context = "runner.cron"
        logger.info(
            "Stopped cron scheduler. home_automation will not run future jobs.", True)


def run_watchdog():
    """Stat watchdog observer."""
    observer = WatchdogObserver()
    observer.schedule(None, HOMEWORK_DIR, True)
    observer.start()
    logger.context = "runner.watchdog"
    logger.info("Started watchdog observer.", True)
    try:
        while True:
            time.sleep(60)
    except ProcessExit:
        observer.stop()
    observer.join()
    logger.context = "runner.watchdog"
    logger.info("Stopped watchdog observer.", True)


@pidfile("home_automation_runner")
def main(cron_user: str = None):
    """Run cron jobs and observe `HOMEWORK_DIR` for changes (blocks permanently)"""
    cron = mp.Process(target=run_cron_jobs, args=tuple(
        [cron_user]), name="home_automation.runner.cron")
    watchdog = mp.Process(target=run_watchdog,
                          name="home_automation.runner.watchdog")
    cron.start()
    watchdog.start()

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, ProcessExit):  # pylint: disable=broad-except
        cron.terminate()
        watchdog.terminate()

    while True:
        time.sleep(1)
        if not cron.is_alive() and not watchdog.is_alive():
            break

    cron.close()
    watchdog.close()


if __name__ == "__main__":
    setup()
    main()
