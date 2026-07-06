import logging
import os
import tempfile
import unittest
from unittest import mock

from juriscraper.lib import log_tools


class LogToolsTest(unittest.TestCase):
    """Tests for default log location fallback and logger creation."""

    def test_env_var_takes_precedence(self):
        with mock.patch.dict(
            os.environ, {"JURISCRAPER_LOG": "/tmp/custom.log"}
        ):
            self.assertEqual(
                log_tools.default_log_location(), "/tmp/custom.log"
            )

    def test_system_dir_used_when_writable(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JURISCRAPER_LOG", None)
            with mock.patch(
                "juriscraper.lib.log_tools.os.access", return_value=True
            ):
                self.assertEqual(
                    log_tools.default_log_location(),
                    os.path.join(log_tools.SYSTEM_LOG_DIR, "debug.log"),
                )

    def test_falls_back_to_user_cache_dir(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JURISCRAPER_LOG", None)
            with mock.patch(
                "juriscraper.lib.log_tools.os.access", return_value=False
            ):
                expected = os.path.join(
                    os.path.expanduser("~"),
                    ".cache",
                    "juriscraper",
                    "debug.log",
                )
                self.assertEqual(log_tools.default_log_location(), expected)

    def test_make_default_logger_creates_missing_directory(self):
        logger = logging.getLogger("juriscraper.lib.log_tools")
        saved_handlers = logger.handlers[:]
        logger.handlers.clear()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                file_path = os.path.join(tmp, "nested", "debug.log")
                result = log_tools.make_default_logger(file_path)
                self.assertTrue(os.path.isdir(os.path.dirname(file_path)))
                self.assertTrue(
                    any(
                        isinstance(h, logging.handlers.RotatingFileHandler)
                        for h in result.handlers
                    )
                )
        finally:
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()
            logger.handlers.extend(saved_handlers)


if __name__ == "__main__":
    unittest.main()
