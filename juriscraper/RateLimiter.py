import threading
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

import pytz


class RateLimiter:
    """
    Rate limiter that handles different limits per site/domain.
    Includes support for working hours.
    """

    def __init__(self):
        self._locks = defaultdict(threading.Lock)
        self._last_request_time = defaultdict(float)
        self._request_counts = defaultdict(list)

    def check_working_hours(
        self, working_hours_config: dict[str, Any]
    ) -> bool:
        """
        Checks if we are within the allowed working hours.

        Args:
            working_hours_config: Working hours config with keys:
                - 'timezone': site's timezone (e.g. 'US/Eastern')
                - 'start_hour': start hour (0-23)
                - 'end_hour': end hour (0-23)
                - 'days': list of allowed days (0=Monday, 6=Sunday)
                - 'respect_weekends': boolean, whether to respect weekends

        Returns:
            True if within allowed hours, False otherwise
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

        # Check hours
        start_hour = working_hours_config.get("start_hour", 0)
        end_hour = working_hours_config.get("end_hour", 23)

        if start_hour <= end_hour:
            # Normal hours (e.g. 6 to 18)
            return start_hour <= current_hour <= end_hour
        else:
            # Hours that cross midnight (e.g. 22 to 6)
            return current_hour >= start_hour or current_hour <= end_hour

    def wait_if_needed(
        self, site_key: str, rate_config: Optional[dict[str, Any]] = None
    ):
        """
        Waits if needed before making a request according to rate limiting config.

        Args:
            site_key: Unique site identifier (e.g. 'ca1', 'pawd', etc.)
            rate_config: Rate limiting config with keys:
                - 'delay': seconds between requests
                - 'max_requests': max number of requests
                - 'time_window': time window in seconds
                - 'working_hours': working hours config
        """
        if not rate_config:
            return

        # Check working hours first
        if "working_hours" in rate_config:
            working_hours_config = rate_config["working_hours"]
            if not self.check_working_hours(working_hours_config):
                if working_hours_config.get("strict", True):
                    # Strict mode: raise an exception
                    raise Exception(
                        f"Attempted to download outside of working hours on {site_key}"
                    )
                else:
                    # Permissive mode: just warn
                    print(
                        f"Warning: Making request to {site_key} outside working hours"
                    )

        with self._locks[site_key]:
            current_time = time.time()

            # Simple delay rate limiting
            if "delay" in rate_config:
                delay = rate_config["delay"]
                last_time = self._last_request_time[site_key]
                elapsed = current_time - last_time

                if elapsed < delay:
                    sleep_time = delay - elapsed
                    time.sleep(sleep_time)
                    current_time = time.time()

            # Windowed rate limiting
            if "max_requests" in rate_config and "time_window" in rate_config:
                max_requests = rate_config["max_requests"]
                time_window = rate_config["time_window"]

                # Remove old requests
                cutoff_time = current_time - time_window
                self._request_counts[site_key] = [
                    req_time
                    for req_time in self._request_counts[site_key]
                    if req_time > cutoff_time
                ]

                # Check if we can make the request
                if len(self._request_counts[site_key]) >= max_requests:
                    # Calculate wait time
                    oldest_request = min(self._request_counts[site_key])
                    wait_time = time_window - (current_time - oldest_request)
                    if wait_time > 0:
                        time.sleep(wait_time)
                        current_time = time.time()

                # Register the new request
                self._request_counts[site_key].append(current_time)

            # Update last request time
            self._last_request_time[site_key] = current_time


# Global rate limiter instance
global_rate_limiter = RateLimiter()
