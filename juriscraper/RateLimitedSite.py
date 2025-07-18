from juriscraper.RateLimiter import global_rate_limiter


class RateLimitedSite:
    """
    Base mixin to add rate limiting to JuriScraper sites.

    Example RATE_LIMIT_CONFIG:
            {
                'delay': 0.5, # Delay in seconds between requests
                'max_requests': 20, # Maximum requests allowed in the time window
                'time_window': 60, # Time window in seconds for rate limiting
                'working_hours': {
                    'timezone': 'US/Eastern', # Timezone for working hours
                    'start_hour': 6, # Start hour (0-23)
                    'end_hour': 18, # End hour (0-23)
                    'days': [0, 1, 2, 3, 4], # Allowed days (0=Monday, 6=Sunday)
                    'respect_weekends': True, # Whether to respect weekends
                    'strict': True # Whether to strictly enforce working hours
                }
            }
    """

    RATE_LIMIT_CONFIG = None

    def get_rate_limit_config(self):
        """Returns the rate limit config for this site."""
        return self.RATE_LIMIT_CONFIG

    def apply_rate_limit(self):
        """
        Applies rate limiting before making requests.
        """
        config = self.get_rate_limit_config()
        if config:
            site_key = getattr(self, "court_id", self.__class__.__name__)
            global_rate_limiter.wait_if_needed(site_key, config)

    def apply_working_hours(self):
        """
        Checks if the request is within working hours.
        Raises an exception if outside working hours.
        """
        config = self.get_rate_limit_config()
        if config and "working_hours" in config:
            global_rate_limiter.check_working_hours(config["working_hours"])
