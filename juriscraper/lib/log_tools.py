import getpass
import logging.handlers
import os
import sys
import traceback

SYSTEM_LOG_DIR = "/var/log/juriscraper"


def default_log_location():
    """Pick a log path that is likely to be writable.

    Order of preference: the JURISCRAPER_LOG environment variable, the
    traditional /var/log/juriscraper location when that directory is
    writable (typical on provisioned servers), and finally a per-user
    cache directory that make_default_logger can create.
    """
    env_path = os.environ.get("JURISCRAPER_LOG")
    if env_path:
        return env_path
    if os.access(SYSTEM_LOG_DIR, os.W_OK):
        return os.path.join(SYSTEM_LOG_DIR, "debug.log")
    return os.path.join(
        os.path.expanduser("~"), ".cache", "juriscraper", "debug.log"
    )


LOG_FILENAME = default_log_location()


def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def make_default_logger(file_path=LOG_FILENAME):
    """Boilerplate and testing code to create a logger. If we run into an
    IOError, issue a warning and use the NullHandler so things work without
    functional logging.

    :return: a logger object
    """
    logger = logging.getLogger(__name__)
    if not len(logger.handlers):
        logger.setLevel(logging.DEBUG)
        # Create a handler and attach it to the logger
        try:
            log_dir = os.path.dirname(file_path)
            if log_dir and not os.path.isdir(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            handler = logging.handlers.RotatingFileHandler(
                file_path, maxBytes=5120000, backupCount=7
            )
        except OSError as e:
            if e.errno == 2:
                errprint(
                    "\nWarning: %s: %s. "
                    "Have you created the directory for the log?"
                    % (
                        e.strerror,
                        file_path,
                    )
                )
            elif e.errno == 13:
                errprint(
                    "\nWarning: %s: %s. "
                    "Cannot access file as user: %s"
                    % (
                        e.strerror,
                        file_path,
                        getpass.getuser(),
                    )
                )
            else:
                errprint(
                    "\nIOError [%s]: %s\n%s"
                    % (e.errno, e.strerror, traceback.format_exc())
                )
            errprint(
                "Juriscraper will continue to run, and all logs will be "
                "sent to stderr."
            )
            handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
        )
        logger.addHandler(handler)
    return logger
