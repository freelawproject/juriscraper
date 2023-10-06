import random
import time


def add_delay(delay=0, deviation=0):
    """Create a semi-random delay.

    Delay is the number of seconds your program will be stopped for, and
    deviation is the number of seconds that the delay can vary.
    """
    from juriscraper.AbstractSite import logger

    duration = random.randrange(delay - deviation, delay + deviation)
    logger.info(f"Adding a delay of {duration} seconds. Please wait.")
    time.sleep(duration)
