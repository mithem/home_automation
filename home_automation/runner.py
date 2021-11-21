"""Schedule appropriate cron jobs and run them (blocks permanently)"""
import os
import time
import multiprocessing as mp
import logging
import logging.handlers
import signal
import sys
from pid.decorator import pidfile

from crontab import CronTab
from watchdog.observers import Observer as WatchdogObserver
from watchdog.events import (
        FileModifiedEvent,
        FileMovedEvent,
        FileDeletedEvent,
        DirModifiedEvent,
        FileSystemEventHandler
        )

from home_automation.config import load_dotenv
from home_automation import compression_manager

# logging system copied from
# https://fanchenbao.medium.com/python3-logging-with-multiprocessing-f51f460b8778

load_dotenv()

CRONTAB_FILE_NAME = "home_automation.tab"
LOG_DIR = os.environ.get("LOG_DIR", os.curdir)
HOMEWORK_DIR = os.environ.get("HOMEWORK_DIR")
ARCHIVE_DIR = os.environ.get("ARCHIVE_DIR")
MOODLE_DL_DIR = os.environ.get("MOODLE_DL_DIR")
PID_FILE_NAME = "home_automation.runner"
TERM_SWITCH = False


class LockError(Exception):
    """An error representing an anomaly handling the lock."""


class _ProcessExit(Exception):
    """An error indicating the process should stop when thrown."""


class _WatchdogEventHandler(FileSystemEventHandler):
    def act(self): # pylint: disable=no-self-use
        """React to a event triggering compression of HOMEWORK_DIR"""
        # this is so much simpler than observing file size over time
        # or implementing inotify etc. and does the job just fine
        time.sleep(5)
        compression_manager.run_main()

    def dispatch(self, event):
        event_types = [FileModifiedEvent, FileMovedEvent, FileDeletedEvent, DirModifiedEvent]
        for event_type in event_types:
            if isinstance(event, event_type):
                self.act()
                break


def _signal_handler(num, frame):  # pylint: disable=unused-argument
    """Respond to signal. Supports: SIGINT, SIGTERM."""
    supported = [
            signal.SIGINT,
            signal.SIGTERM
    ]
    if num in supported:
        raise _ProcessExit()


def _configure_log_listener():
    root = logging.getLogger()
    file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, "home_automation_runner.log"))
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
            "%(asctime)s %(processName)-10s %(levelname)-8s %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.setLevel(logging.DEBUG)


def _logging_listener(queue: mp.Queue):
    def handle_logs():
        while not queue.empty():
            record = queue.get()
            logger = logging.getLogger(record.name)
            logger.handle(record)

    try:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
        _configure_log_listener()
        while True:
            handle_logs()
            time.sleep(1)
    except (KeyboardInterrupt, _ProcessExit):
        time.sleep(3) # for the "piped" processes to stop first
        sys.exit(0)


def _configure_log_worker(queue: mp.Queue):
    queue_handler = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(queue_handler)
    root.setLevel(logging.DEBUG)


def setup():
    """Set up local filesystem for home_automation (create necessary dirs)
    and register signal handler."""
    for path in [HOMEWORK_DIR, ARCHIVE_DIR, LOG_DIR]:
        try:
            os.makedirs(path)
        except FileExistsError:
            continue
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)


def run_cron_jobs(queue: mp.Queue, cron_user: str = None):
    """Schedule cron jobs and run them."""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    _configure_log_worker(queue)
    logger = logging.getLogger("home_automation_runner_cron")
    if not cron_user:
        cron_user = os.environ.get("CRON_USER")

    def load_crontab():
        cron = CronTab(user=cron_user, tabfile=CRONTAB_FILE_NAME)
        return cron

    try:
        cron = load_crontab()
    except FileNotFoundError:
        with open(CRONTAB_FILE_NAME, "w", encoding="utf-8"):
            pass
        cron = load_crontab()

    cron.remove_all()

    archiving_job = cron.new(
            command="python3 -m home_automation.archive_manager archive")
    reorganization_job = cron.new(
            command="python3 -m home_automation.archive_manager reorganize")
    if MOODLE_DL_DIR is not None and not os.path.isdir(MOODLE_DL_DIR):
        raise Exception(f"Directory not found: {MOODLE_DL_DIR}")
    moodle_dl_job = cron.new(command=f"python3 -m moodle-dl --path '{MOODLE_DL_DIR}'")

    archiving_job.minute.on(0)
    archiving_job.hour.on(0)
    archiving_job.dow.on("SAT")

    reorganization_job.minute.on(0)
    reorganization_job.hour.on(0)
    reorganization_job.day.on(1)

    moodle_dl_job.minute.on(0)
    moodle_dl_job.hour.every(1)

    cron.write()  # not sure if I could run the scheduler without writing the file

    logger.info("Running cron jobs until interrupted...")
    try:
        for result in cron.run_scheduler():
            logger.info("Ran cron job. Ouput: %s", result)
    except (KeyboardInterrupt, _ProcessExit):
        logger.info(
                "Stopped cron scheduler. home_automation will not run future jobs.")
        sys.exit(0)


def run_watchdog(queue: mp.Queue):
    """Start watchdog observer. Even before the first event, simulate one in order
    to compress uncompressed files."""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    _configure_log_worker(queue)
    logger = logging.getLogger("home_automation_runner_watchdog")
    event_handler = _WatchdogEventHandler()
    observer = WatchdogObserver()
    observer.schedule(event_handler, HOMEWORK_DIR, True)
    observer.start()
    logger.info("Started watchdog observer.")
    logger.info("Simulating first event on startup.") # yes, 'simulate' is a strong word
    event_handler.act()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, _ProcessExit):
        observer.stop()
        observer.join()
        logger.info("Stopped watchdog observer.")
        sys.exit(0)

def run_backend_server(queue: mp.Queue):
    """Run the WSGI gunicorn server (not the frontend)."""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    _configure_log_worker(queue)
    logger = logging.getLogger("home_automation_backend")
    logger.info("Running backend...")
    try:
        # sometimes running gunicorn from shell is just equivalent to but way easier than
        # reverse-engineering gunicorn to get an appropriate entrypoint

        # only bind to localhost so the API isn't exposed outside (if
        # I need that at any point, an https proxy is a way better idea)

        # proxy for certificate management (don't want to re-configure 20 services
        # once the certificate changes)
        os.system("python3 -m gunicorn --pid /var/run/home_automation/gunicorn.pid -w 2 --bi\
nd 127.0.0.1:10001 'home_automation.server.backend:create_app()'")
    except (KeyboardInterrupt, _ProcessExit):
        logger.info("Stopped gunicorn (backend).")
        sys.exit(0)

def build_frontend(queue: mp.Queue):
    """Build the frontend React app (not the backend and don't serve it (that's nginx's job.))."""
    _configure_log_worker(queue)
    logger = logging.getLogger("home_automation_frontend")
    logger.info("Building frontend.")
    try:
        os.system("cd home_automation/server/frontend && yarn build")
        logger.info("Built frontend.")
    except (KeyboardInterrupt, _ProcessExit):
        logger.info("Aborted frontend build.")
        sys.exit(0)

@pidfile("/var/run/home_automation/runner.pid")
def main(cron_user: str = None):
    """Run cron jobs and observe `HOMEWORK_DIR` for changes (blocks permanently)"""
    queue: mp.Queue = mp.Queue(-1)
    processes = [
            mp.Process(target=_logging_listener, args=(queue,),
                name="home_automation.runner.log_listener"),
            mp.Process(target=run_cron_jobs, args=(queue, cron_user),
                name="home_automation.runner.cron"),
            mp.Process(target=run_watchdog, args=(queue,),
                name="home_automation.runner.watchdog"),
            mp.Process(target=run_backend_server, args=(queue,),
                name="home_automation.runner.backend"),
            mp.Process(target=build_frontend, args=(queue,),
                name="home_automation.runner.frontend")
            ]
    for process in processes:
        process.start()

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, _ProcessExit):  # pylint: disable=broad-except
        try:
            os.kill(os.getpid(), signal.SIGTERM)
        except _ProcessExit:
            pass
        for process in processes:
            process.terminate()

    while True:
        time.sleep(1)
        alive = False
        for process in processes:
            if process.is_alive():
                alive = True
        if not alive:
            break

    for process in processes:
        process.terminate()
    sys.exit(0)


if __name__ == "__main__":
    setup()
    main()
