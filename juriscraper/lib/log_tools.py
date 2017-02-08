import getpass
import logging.handlers
import traceback

import sys

LOG_FILENAME = '/var/log/juriscraper/debug.log'


def make_default_logger(file_path=LOG_FILENAME):
    """Boilerplate and testing code to create a logger. If we run into an
    IOError, issue a warning and use the NullHandler so things work without
    functional logging.

    :return: a logger object
    """
    logger = logging.getLogger('Logger')
    if not len(logger.handlers):
        logger.setLevel(logging.DEBUG)
        # Create a handler and attach it to the logger
        try:
            handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=5120000,
                backupCount=7
            )
        except IOError as e:
            if e.errno == 2:
                print("\nWarning: %s: %s. " \
                      "Have you created the directory for the log?" % (
                          e.strerror,
                          file_path,
                      ))
            elif e.errno == 13:
                print("\nWarning: %s: %s. " \
                      "Cannot access file as user: %s" % (
                          e.strerror,
                          file_path,
                          getpass.getuser(),
                      ))
            else:
                print("\nIOError [%s]: %s\n%s" % (
                    e.errno,
                    e.strerror,
                    traceback.format_exc()
                ))
            print("Juriscraper will continue to run, and all logs will be "
                  "sent to stdout.")
            handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
        )
        logger.addHandler(handler)
    return logger
