import random
import time

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

from juriscraper.AbstractSite import logger


class SSLAdapter(HTTPAdapter):
    """An HTTPS Transport Adapter that uses an arbitrary SSL version."""

    def __init__(self, ssl_version=None, **kwargs):
        self.ssl_version = ssl_version

        super(SSLAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=self.ssl_version,
        )


def add_delay(delay=0, deviation=0):
    """Create a semi-random delay.

    Delay is the number of seconds your program will be stopped for, and
    deviation is the number of seconds that the delay can vary.
    """
    duration = random.randrange(delay - deviation, delay + deviation)
    logger.info("Adding a delay of %s seconds. Please wait." % duration)
    time.sleep(duration)
