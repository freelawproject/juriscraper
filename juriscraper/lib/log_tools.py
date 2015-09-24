import getpass
import logging.handlers
import traceback

LOG_FILENAME = '/var/log/juriscraper/debug.log'


def make_default_logger(file_path=LOG_FILENAME):
    """Boilerplate and testing code to create a logger. If we run into an
    IOError, issue a warning and use the NullHandler so things work without
    functional logging.

    :return: a logger object
    """
    logger = logging.getLogger('Logger')
    logger.setLevel(logging.DEBUG)
    # Create a handler and attach it to the logger
    try:
        handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=5120000,
            backupCount=7
        )
    except IOError, e:
        if e.errno == 2:
            print "\nWarning: %s: %s. " \
                  "Have you created the directory for the log?" % (
                      e.strerror,
                      file_path,
                  )
        elif e.errno == 13:
            print "\nWarning: %s: %s. " \
                  "Cannot access file as user: %s" % (
                      e.strerror,
                      file_path,
                      getpass.getuser(),
                  )
        else:
            print "\nIOError [%s]: %s\n%s" % (
                e.errno,
                e.strerror,
                traceback.format_exc()
            )
        print "Juriscraper will continue to run, but will not create logs."
        handler = logging.NullHandler()

    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
    )
    logger.addHandler(handler)

    return logger
