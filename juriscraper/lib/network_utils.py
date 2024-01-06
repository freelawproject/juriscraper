import random
import time

from juriscraper.AbstractSite import logger


def add_delay(delay=0, deviation=0):
    """Create a semi-random delay.

    Delay is the number of seconds your program will be stopped for, and
    deviation is the number of seconds that the delay can vary.
    """
    duration = random.randrange(delay - deviation, delay + deviation)
    logger.info(f"Adding a delay of {duration} seconds. Please wait.")
    time.sleep(duration)
