import random
import ssl
import time

from requests.adapters import HTTPAdapter
from urllib3.util import create_urllib3_context


class SSLAdapter(HTTPAdapter):
    def __init__(
        self, ssl_version=ssl.PROTOCOL_TLSv1_2, ciphers=None, **kwargs
    ):
        self.ssl_version = ssl_version or ssl.PROTOCOL_TLS
        self.ssl_context = create_urllib3_context(
            ssl_version=self.ssl_version, ciphers=ciphers
        )
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)


def add_delay(delay=0, deviation=0):
    """Create a semi-random delay.

    Delay is the number of seconds your program will be stopped for, and
    deviation is the number of seconds that the delay can vary.
    """
    from juriscraper.AbstractSite import logger

    duration = random.randrange(delay - deviation, delay + deviation)
    logger.info(f"Adding a delay of {duration} seconds. Please wait.")
    time.sleep(duration)
