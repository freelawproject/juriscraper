import logging
from datetime import datetime
from typing import Any

import pytz

logger = logging.getLogger(__name__)


class RateLimited:
    """
    Base mixin to add rate limiting to JuriScraper sites.

    Example RATE_LIMIT_CONFIG with single time window:
            {
                #more to be added
                'working_hours': {
                    'timezone': 'US/Eastern', # Timezone for working hours
                    'start_hour': 6, # Start hour (0-23)
                    'end_hour': 18, # End hour (0-23)
                    'days': [0, 1, 2, 3, 4], # Allowed days (0=Monday, 6=Sunday)
                    'respect_weekends': True, # Whether to respect weekends
                }
            }

    Example RATE_LIMIT_CONFIG with multiple time windows:
            {
                #more to be added
                'working_hours': {
                    'timezone': 'US/Eastern', # Timezone for working hours
                    'windows': [  # Multiple time windows
                        {'start_hour': 6, 'end_hour': 10},   # Morning window
                        {'start_hour': 14, 'end_hour': 18},  # Afternoon window
                    ],
                    'days': [0, 1, 2, 3, 4], # Allowed days (0=Monday, 6=Sunday)
                    'respect_weekends': True, # Whether to respect weekends
                }
            }
    """

    RATE_LIMIT_CONFIG = None

    def get_rate_limit_config(self):
        """Returns the rate limit config for this site."""
        return self.RATE_LIMIT_CONFIG

    def apply_working_hours(self) -> bool:
        """
        Checks if the request is within working hours.

        Returns:
            True if within working hours or no config is set.
            False if outside working hours.
        """
        config = self.get_rate_limit_config()
        if (
            config
            and "working_hours" in config
            and not self._check_working_hours(config["working_hours"])
        ):
            logger.info("Request is outside of allowed working hours")
            return False
        return True

    @staticmethod
    def _check_time_window(
        current_hour: int, start_hour: int, end_hour: int
    ) -> bool:
        """
        Check if current hour falls within a time window.

        :param: current_hour: Current hour (0-23)
        :param: start_hour: Start hour of window (0-23)
        :param: end_hour: End hour of window (0-23)

        :return: True if current hour is within the window, False otherwise
        """
        if start_hour <= end_hour:
            # Normal hours (e.g. 6 to 18)
            return start_hour <= current_hour <= end_hour
        else:
            # Hours that cross midnight (e.g. 22 to 6)
            return current_hour >= start_hour or current_hour <= end_hour

    @staticmethod
    def _check_working_hours(working_hours_config: dict[str, Any]) -> bool:
        """
        Checks if we are within the allowed working hours.

        :param: working_hours_config: Working hours config with keys:
            - 'timezone': site's timezone (e.g. 'US/Eastern')
            - 'start_hour': start hour (0-23) - used if 'windows' not present
            - 'end_hour': end hour (0-23) - used if 'windows' not present
            - 'windows': list of time windows with 'start_hour' and 'end_hour'
            - 'days': list of allowed days (0=Monday, 6=Sunday)
            - 'respect_weekends': boolean, whether to respect weekends

        :return: True if within allowed hours, False otherwise
        """
        tz_name = working_hours_config.get("timezone", "UTC")
        try:
            tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            # If timezone is not recognized, use UTC
            tz = pytz.UTC

        current_time = datetime.now(tz)
        current_hour = current_time.hour
        current_day = current_time.weekday()  # 0=Monday, 6=Sunday

        # Check allowed days
        if "days" in working_hours_config:
            allowed_days = working_hours_config["days"]
            if current_day not in allowed_days:
                return False

        # Check weekends (Saturday=5, Sunday=6)
        if working_hours_config.get(
            "respect_weekends", False
        ) and current_day in [5, 6]:
            return False

        # Check hours - support both single window and multiple windows
        if "windows" in working_hours_config:
            # Multiple time windows
            windows = working_hours_config["windows"]
            for window in windows:
                start_hour = window.get("start_hour", 0)
                end_hour = window.get("end_hour", 23)
                if RateLimited._check_time_window(
                    current_hour, start_hour, end_hour
                ):
                    return True
            # If no window matched, we're outside working hours
            return False
        else:
            # Single time window
            start_hour = working_hours_config.get("start_hour", 0)
            end_hour = working_hours_config.get("end_hour", 23)
            return RateLimited._check_time_window(
                current_hour, start_hour, end_hour
            )
