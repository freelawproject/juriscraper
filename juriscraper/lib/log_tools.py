from __future__ import print_function

import getpass
import logging.handlers
import traceback

import sys

LOG_FILENAME = "/var/log/juriscraper/debug.log"


def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def make_default_logger(file_path=LOG_FILENAME):
    """Boilerplate and testing code to create a logger. If we run into an
    IOError, issue a warning and use the NullHandler so things work without
    functional logging.

    :return: a logger object
    """
    logger = logging.getLogger("Logger")
    if not len(logger.handlers):
        logger.setLevel(logging.DEBUG)
        # Create a handler and attach it to the logger
        try:
            handler = logging.handlers.RotatingFileHandler(
                file_path, maxBytes=5120000, backupCount=7
            )
        except IOError as e:
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
