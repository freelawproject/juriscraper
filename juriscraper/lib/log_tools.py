import getpass
import logging.handlers
import os
import sys
import traceback

LOG_FILENAME = os.environ.get(
    "JURISCRAPER_LOG", "/var/log/juriscraper/debug.log"
)


def _errprint(message: str) -> None:
    print(message, file=sys.stderr)


def make_default_logger(file_path: str = LOG_FILENAME) -> logging.Logger:
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
            handler = logging.handlers.RotatingFileHandler(
                file_path, maxBytes=5120000, backupCount=7
            )
        except OSError as e:
            if e.errno == 2:
                _errprint(
                    "\nWarning: %s: %s. "
                    "Have you created the directory for the log?"
                    % (
                        e.strerror,
                        file_path,
                    )
                )
            elif e.errno == 13:
                _errprint(
                    "\nWarning: %s: %s. "
                    "Cannot access file as user: %s"
                    % (
                        e.strerror,
                        file_path,
                        getpass.getuser(),
                    )
                )
            else:
                _errprint(
                    "\nIOError [%s]: %s\n%s"
                    % (e.errno, e.strerror, traceback.format_exc())
                )
            _errprint(
                "Juriscraper will continue to run, and all logs will be "
                "sent to stderr."
            )
            handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
        )
        logger.addHandler(handler)
    return logger


def log_error(
    logger: logging.Logger,
    key: str,
    msg: str,
    *args: object,
    court_id: str | None = None,
    url: str | None = None,
    group_by: str = "court",
    exc_info: bool | BaseException | None = False,
    **extra: object,
) -> None:
    """Log an error with the `extra` keys that group it in Sentry

    CourtListener copies `extra["fingerprint"]` into the Sentry event, so
    every call with the same key (and court, when `group_by` is "court")
    lands in one issue no matter how the message varies.

    Use "%s" placeholders in `msg`, never f-strings, so the message itself
    stays stable too.

    :param key: short stable name for the error, e.g. "zero-results"
    :param court_id: the scraper's `court_id`, when there is one
    :param url: the page involved, when there is one
    :param group_by: "court" groups by key and court; "shared" groups by key
        only, for errors in shared code where one ticket covers all courts
    :param exc_info: forwarded to `logger.error`
    :param extra: more values to show on the Sentry event
    """
    fingerprint = [key] if group_by == "shared" else [key, court_id or ""]
    extra.update(
        {"fingerprint": fingerprint, "court_id": court_id, "url": url}
    )
    # stacklevel=2 keeps the caller's file and line on the log record
    logger.error(msg, *args, extra=extra, exc_info=exc_info, stacklevel=2)
