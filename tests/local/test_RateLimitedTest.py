#!/usr/bin/env python

import unittest
from datetime import datetime
from unittest.mock import patch

from juriscraper.RateLimited import RateLimited


class RateLimitedTest(unittest.TestCase):
    """Test cases for the RateLimited mixin class."""

    def test_single_time_window_within_hours(self):
        """Test that single time window returns True when within hours."""
        config = {
            "timezone": "US/Eastern",
            "start_hour": 6,
            "end_hour": 18,
            "days": [0, 1, 2, 3, 4],  # Monday-Friday
        }

        # Mock current time to be within working hours (10 AM on Monday)
        mock_time = datetime(2025, 12, 8, 10, 0, 0)  # Monday
        with patch("juriscraper.RateLimited.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            result = RateLimited._check_working_hours(config)
            self.assertTrue(result)

    def test_single_time_window_outside_hours(self):
        """Test that single time window returns False when outside hours."""
        config = {
            "timezone": "US/Eastern",
            "start_hour": 6,
            "end_hour": 18,
            "days": [0, 1, 2, 3, 4],  # Monday-Friday
        }

        # Mock current time to be outside working hours (8 PM on Monday)
        mock_time = datetime(2025, 12, 8, 20, 0, 0)  # Monday, 8 PM
        with patch("juriscraper.RateLimited.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            result = RateLimited._check_working_hours(config)
            self.assertFalse(result)

    def test_multiple_time_windows_within_window(self):
        """Test multiple windows when time falls in one window."""
        config = {
            "timezone": "US/Eastern",
            "windows": [
                {"start_hour": 6, "end_hour": 10},  # Morning window
            ],
            "days": [0, 1, 2, 3, 4],
        }

        # Mock time at 8 AM (within first window)
        mock_time = datetime(2025, 12, 8, 8, 0, 0)  # Monday, 8 AM
        with patch("juriscraper.RateLimited.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            result = RateLimited._check_working_hours(config)
            self.assertTrue(result)

    def test_multiple_time_windows_between_windows(self):
        """Test multiple windows when time falls between windows."""
        config = {
            "timezone": "US/Eastern",
            "windows": [
                {"start_hour": 6, "end_hour": 10},  # Morning window
                {"start_hour": 14, "end_hour": 18},  # Afternoon window
            ],
            "days": [0, 1, 2, 3, 4],
        }

        # Mock time at 12 PM (between windows - lunch time)
        mock_time = datetime(2025, 12, 8, 12, 0, 0)  # Monday, 12 PM
        with patch("juriscraper.RateLimited.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            result = RateLimited._check_working_hours(config)
            self.assertFalse(result)

    def test_weekend_respect(self):
        """Test that weekends are blocked when respect_weekends is True."""
        config = {
            "timezone": "US/Eastern",
            "start_hour": 6,
            "end_hour": 18,
            "respect_weekends": True,
        }

        # Mock time on Saturday
        mock_time = datetime(2025, 12, 13, 10, 0, 0)  # Saturday, 10 AM
        with patch("juriscraper.RateLimited.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            result = RateLimited._check_working_hours(config)
            self.assertFalse(result)

    def test_allowed_days_restriction(self):
        """Test that days not in the allowed list are blocked."""
        config = {
            "timezone": "US/Eastern",
            "start_hour": 6,
            "end_hour": 18,
            "days": [0, 2, 4],  # Monday, Wednesday, Friday (no Tuesday)
        }

        # Mock time on Tuesday
        mock_time = datetime(2025, 12, 9, 10, 0, 0)  # Tuesday, 10 AM
        with patch("juriscraper.RateLimited.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            result = RateLimited._check_working_hours(config)
            self.assertFalse(result)

    def test_midnight_crossing_window(self):
        """Test midnight-crossing window (22:00 to 6:00) works correctly."""
        config = {
            "timezone": "US/Eastern",
            "start_hour": 22,
            "end_hour": 6,
        }

        # Mock time at 11 PM (before midnight)
        mock_time = datetime(2025, 12, 8, 23, 0, 0)  # Monday, 11 PM
        with patch("juriscraper.RateLimited.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            result = RateLimited._check_working_hours(config)
            self.assertTrue(result)

    def test_apply_working_hours_no_config(self):
        """Test apply_working_hours returns True when no config is set."""

        class TestSite(RateLimited):
            RATE_LIMIT_CONFIG = None

        site = TestSite()
        result = site.apply_working_hours()
        self.assertTrue(result)

    def test_apply_working_hours_outside_hours(self):
        """Test apply_working_hours returns False and logs when outside hours."""

        class TestSite(RateLimited):
            RATE_LIMIT_CONFIG = {
                "working_hours": {
                    "timezone": "US/Eastern",
                    "start_hour": 6,
                    "end_hour": 18,
                }
            }

        site = TestSite()

        # Mock time at 8 PM on Monday
        mock_time = datetime(2025, 12, 8, 20, 0, 0)
        with patch("juriscraper.RateLimited.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            with patch("juriscraper.RateLimited.logger") as mock_logger:
                result = site.apply_working_hours()
                self.assertFalse(result)
                mock_logger.info.assert_called_once_with(
                    "Request is outside of allowed working hours"
                )

    def test_invalid_timezone_falls_back_to_utc(self):
        """Test that invalid timezone falls back to UTC."""
        config = {
            "timezone": "Invalid/Timezone",
            "start_hour": 6,
            "end_hour": 18,
        }

        # Mock pytz to raise UnknownTimeZoneError
        mock_time = datetime(2025, 12, 8, 10, 0, 0)
        with patch("juriscraper.RateLimited.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            with patch("juriscraper.RateLimited.pytz") as mock_pytz:
                mock_pytz.UnknownTimeZoneError = Exception
                mock_pytz.timezone.side_effect = Exception("Invalid timezone")
                mock_pytz.UTC = "UTC"
                # Should not raise, should fall back to UTC
                RateLimited._check_working_hours(config)
