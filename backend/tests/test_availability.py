"""
Tests for availability calculation service.
Tests edge cases and various scenarios for calculating available time slots.
"""

import pytest
from datetime import datetime, date, time, timedelta, timezone
from app.services.availability import (
    TimeRange,
    expand_weekly_schedule,
    apply_date_exceptions,
    subtract_busy_intervals,
    parse_google_calendar_busy,
    calculate_availability,
)


class TestTimeRange:
    """Test TimeRange dataclass."""

    def test_time_range_creation(self):
        """Test creating a TimeRange."""
        start = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc)
        tr = TimeRange(start=start, end=end)
        assert tr.start == start
        assert tr.end == end

    def test_time_range_timezone_aware(self):
        """Test that TimeRange makes naive datetimes timezone-aware."""
        start = datetime(2024, 1, 1, 10, 0)
        end = datetime(2024, 1, 1, 11, 0)
        tr = TimeRange(start=start, end=end)
        assert tr.start.tzinfo is not None
        assert tr.end.tzinfo is not None

    def test_time_range_overlaps(self):
        """Test overlap detection."""
        tr1 = TimeRange(
            start=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        tr2 = TimeRange(
            start=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc),
        )
        assert tr1.overlaps(tr2) is True
        assert tr2.overlaps(tr1) is True

    def test_time_range_no_overlap(self):
        """Test non-overlapping ranges."""
        tr1 = TimeRange(
            start=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
        )
        tr2 = TimeRange(
            start=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc),
        )
        assert tr1.overlaps(tr2) is False

    def test_time_range_contains(self):
        """Test contains detection."""
        tr1 = TimeRange(
            start=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc),
        )
        tr2 = TimeRange(
            start=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        assert tr1.contains(tr2) is True
        assert tr2.contains(tr1) is False


class TestExpandWeeklySchedule:
    """Test expanding weekly schedule to date ranges."""

    def test_expand_single_day(self):
        """Test expanding schedule for a single day."""
        weekly_schedule = {
            0: [{"start": "09:00", "end": "12:00"}],  # Monday
        }
        start_date = date(2024, 1, 1)  # Monday
        end_date = date(2024, 1, 1)
        
        ranges = expand_weekly_schedule(weekly_schedule, start_date, end_date)
        assert len(ranges) == 1
        assert ranges[0].start.date() == start_date
        assert ranges[0].start.hour == 9
        assert ranges[0].end.hour == 12

    def test_expand_multiple_days(self):
        """Test expanding schedule for multiple days."""
        weekly_schedule = {
            0: [{"start": "09:00", "end": "12:00"}],  # Monday
            2: [{"start": "14:00", "end": "18:00"}],  # Wednesday
        }
        start_date = date(2024, 1, 1)  # Monday
        end_date = date(2024, 1, 3)  # Wednesday
        
        ranges = expand_weekly_schedule(weekly_schedule, start_date, end_date)
        assert len(ranges) == 2
        assert ranges[0].start.date() == date(2024, 1, 1)
        assert ranges[1].start.date() == date(2024, 1, 3)

    def test_expand_multiple_ranges_per_day(self):
        """Test expanding schedule with multiple time ranges per day."""
        weekly_schedule = {
            0: [
                {"start": "09:00", "end": "12:00"},
                {"start": "14:00", "end": "18:00"},
            ],
        }
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        
        ranges = expand_weekly_schedule(weekly_schedule, start_date, end_date)
        assert len(ranges) == 2

    def test_expand_empty_schedule(self):
        """Test expanding empty schedule."""
        weekly_schedule = {}
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        ranges = expand_weekly_schedule(weekly_schedule, start_date, end_date)
        assert len(ranges) == 0

    def test_expand_invalid_time_format(self):
        """Test that invalid time formats are skipped."""
        weekly_schedule = {
            0: [
                {"start": "09:00", "end": "12:00"},
                {"start": "invalid", "end": "12:00"},
                {"start": "14:00", "end": "invalid"},
            ],
        }
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        
        ranges = expand_weekly_schedule(weekly_schedule, start_date, end_date)
        assert len(ranges) == 1  # Only valid range included

    def test_expand_overnight_range(self):
        """Test expanding schedule with overnight time range."""
        weekly_schedule = {
            0: [{"start": "22:00", "end": "02:00"}],  # Overnight
        }
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        
        ranges = expand_weekly_schedule(weekly_schedule, start_date, end_date)
        assert len(ranges) == 1
        assert ranges[0].start.date() == date(2024, 1, 1)
        assert ranges[0].end.date() == date(2024, 1, 2)  # Next day


class TestApplyDateExceptions:
    """Test applying date exceptions."""

    def test_apply_off_exception(self):
        """Test applying 'off' exception removes all ranges for that date."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
            TimeRange(
                start=datetime(2024, 1, 2, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        date_exceptions = {
            date(2024, 1, 1): {"exception_type": "off"},
        }
        
        result = apply_date_exceptions(time_ranges, date_exceptions)
        assert len(result) == 1
        assert result[0].start.date() == date(2024, 1, 2)

    def test_apply_custom_exception(self):
        """Test applying 'custom' exception replaces ranges."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        date_exceptions = {
            date(2024, 1, 1): {
                "exception_type": "custom",
                "custom_hours": [{"start": "14:00", "end": "18:00"}],
            },
        }
        
        result = apply_date_exceptions(time_ranges, date_exceptions)
        assert len(result) == 1
        assert result[0].start.hour == 14
        assert result[0].end.hour == 18

    def test_apply_custom_exception_multiple_ranges(self):
        """Test custom exception with multiple time ranges."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        date_exceptions = {
            date(2024, 1, 1): {
                "exception_type": "custom",
                "custom_hours": [
                    {"start": "10:00", "end": "11:00"},
                    {"start": "15:00", "end": "16:00"},
                ],
            },
        }
        
        result = apply_date_exceptions(time_ranges, date_exceptions)
        assert len(result) == 2

    def test_apply_no_exception(self):
        """Test that ranges without exceptions are kept."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        date_exceptions = {}
        
        result = apply_date_exceptions(time_ranges, date_exceptions)
        assert len(result) == 1
        assert result[0] == time_ranges[0]

    def test_apply_unknown_exception_type(self):
        """Test that unknown exception types keep original ranges."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        date_exceptions = {
            date(2024, 1, 1): {"exception_type": "unknown"},
        }
        
        result = apply_date_exceptions(time_ranges, date_exceptions)
        assert len(result) == 1


class TestSubtractBusyIntervals:
    """Test subtracting busy intervals from available ranges."""

    def test_subtract_no_busy_intervals(self):
        """Test subtracting when there are no busy intervals."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        busy_intervals = []
        
        result = subtract_busy_intervals(time_ranges, busy_intervals)
        assert len(result) == 1
        assert result[0] == time_ranges[0]

    def test_subtract_non_overlapping_busy(self):
        """Test subtracting non-overlapping busy intervals."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        busy_intervals = [
            TimeRange(
                start=datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 14, 0, tzinfo=timezone.utc),
            ),
        ]
        
        result = subtract_busy_intervals(time_ranges, busy_intervals)
        assert len(result) == 1
        assert result[0] == time_ranges[0]

    def test_subtract_fully_overlapping_busy(self):
        """Test subtracting busy interval that fully covers available range."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        busy_intervals = [
            TimeRange(
                start=datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc),
            ),
        ]
        
        result = subtract_busy_intervals(time_ranges, busy_intervals)
        assert len(result) == 0

    def test_subtract_partial_overlap_start(self):
        """Test subtracting busy interval that overlaps at the start."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        busy_intervals = [
            TimeRange(
                start=datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            ),
        ]
        
        result = subtract_busy_intervals(time_ranges, busy_intervals)
        assert len(result) == 1
        assert result[0].start.hour == 10
        assert result[0].end.hour == 12

    def test_subtract_partial_overlap_end(self):
        """Test subtracting busy interval that overlaps at the end."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        busy_intervals = [
            TimeRange(
                start=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc),
            ),
        ]
        
        result = subtract_busy_intervals(time_ranges, busy_intervals)
        assert len(result) == 1
        assert result[0].start.hour == 9
        assert result[0].end.hour == 11

    def test_subtract_busy_in_middle(self):
        """Test subtracting busy interval in the middle splits the range."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        busy_intervals = [
            TimeRange(
                start=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            ),
        ]
        
        result = subtract_busy_intervals(time_ranges, busy_intervals)
        assert len(result) == 2
        assert result[0].start.hour == 9
        assert result[0].end.hour == 10
        assert result[1].start.hour == 11
        assert result[1].end.hour == 12

    def test_subtract_multiple_busy_intervals(self):
        """Test subtracting multiple busy intervals."""
        time_ranges = [
            TimeRange(
                start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 18, 0, tzinfo=timezone.utc),
            ),
        ]
        busy_intervals = [
            TimeRange(
                start=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            ),
            TimeRange(
                start=datetime(2024, 1, 1, 14, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 15, 0, tzinfo=timezone.utc),
            ),
        ]
        
        result = subtract_busy_intervals(time_ranges, busy_intervals)
        assert len(result) == 3
        # Verify the ranges are correct
        assert result[0].end.hour == 10
        assert result[1].start.hour == 11
        assert result[1].end.hour == 14
        assert result[2].start.hour == 15


class TestParseGoogleCalendarBusy:
    """Test parsing Google Calendar freebusy results."""

    def test_parse_single_busy_interval(self):
        """Test parsing a single busy interval."""
        freebusy_result = {
            "calendars": {
                "calendar_id": {
                    "busy": [
                        {
                            "start": "2024-01-01T10:00:00Z",
                            "end": "2024-01-01T11:00:00Z",
                        }
                    ]
                }
            }
        }
        
        result = parse_google_calendar_busy(freebusy_result)
        assert len(result) == 1
        assert result[0].start.hour == 10
        assert result[0].end.hour == 11

    def test_parse_multiple_busy_intervals(self):
        """Test parsing multiple busy intervals."""
        freebusy_result = {
            "calendars": {
                "calendar_id": {
                    "busy": [
                        {
                            "start": "2024-01-01T10:00:00Z",
                            "end": "2024-01-01T11:00:00Z",
                        },
                        {
                            "start": "2024-01-01T14:00:00Z",
                            "end": "2024-01-01T15:00:00Z",
                        },
                    ]
                }
            }
        }
        
        result = parse_google_calendar_busy(freebusy_result)
        assert len(result) == 2

    def test_parse_specific_calendar_id(self):
        """Test parsing with specific calendar ID."""
        freebusy_result = {
            "calendars": {
                "calendar_1": {
                    "busy": [
                        {
                            "start": "2024-01-01T10:00:00Z",
                            "end": "2024-01-01T11:00:00Z",
                        }
                    ]
                },
                "calendar_2": {
                    "busy": [
                        {
                            "start": "2024-01-01T14:00:00Z",
                            "end": "2024-01-01T15:00:00Z",
                        }
                    ]
                },
            }
        }
        
        result = parse_google_calendar_busy(freebusy_result, calendar_id="calendar_2")
        assert len(result) == 1
        assert result[0].start.hour == 14

    def test_parse_empty_busy(self):
        """Test parsing empty busy intervals."""
        freebusy_result = {
            "calendars": {
                "calendar_id": {
                    "busy": []
                }
            }
        }
        
        result = parse_google_calendar_busy(freebusy_result)
        assert len(result) == 0

    def test_parse_no_calendars(self):
        """Test parsing when no calendars in result."""
        freebusy_result = {
            "calendars": {}
        }
        
        result = parse_google_calendar_busy(freebusy_result)
        assert len(result) == 0

    def test_parse_invalid_datetime_format(self):
        """Test that invalid datetime formats are skipped."""
        freebusy_result = {
            "calendars": {
                "calendar_id": {
                    "busy": [
                        {
                            "start": "2024-01-01T10:00:00Z",
                            "end": "2024-01-01T11:00:00Z",
                        },
                        {
                            "start": "invalid",
                            "end": "2024-01-01T12:00:00Z",
                        },
                    ]
                }
            }
        }
        
        result = parse_google_calendar_busy(freebusy_result)
        assert len(result) == 1  # Only valid interval included


class TestCalculateAvailability:
    """Test the main calculate_availability function."""

    def test_calculate_simple_availability(self):
        """Test calculating availability with simple schedule."""
        weekly_schedule = {
            0: [{"start": "09:00", "end": "12:00"}],  # Monday
        }
        date_exceptions = {}
        busy_intervals = []
        start_date = date(2024, 1, 1)  # Monday
        end_date = date(2024, 1, 1)
        
        result = calculate_availability(
            weekly_schedule=weekly_schedule,
            date_exceptions=date_exceptions,
            busy_intervals=busy_intervals,
            start_date=start_date,
            end_date=end_date,
        )
        assert len(result) == 1
        assert result[0].start.hour == 9
        assert result[0].end.hour == 12

    def test_calculate_with_date_exception_off(self):
        """Test calculating availability with 'off' date exception."""
        weekly_schedule = {
            0: [{"start": "09:00", "end": "12:00"}],  # Monday
        }
        date_exceptions = {
            date(2024, 1, 1): {"exception_type": "off"},
        }
        busy_intervals = []
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        
        result = calculate_availability(
            weekly_schedule=weekly_schedule,
            date_exceptions=date_exceptions,
            busy_intervals=busy_intervals,
            start_date=start_date,
            end_date=end_date,
        )
        assert len(result) == 0

    def test_calculate_with_busy_interval(self):
        """Test calculating availability with busy interval."""
        weekly_schedule = {
            0: [{"start": "09:00", "end": "12:00"}],  # Monday
        }
        date_exceptions = {}
        busy_intervals = [
            TimeRange(
                start=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
            ),
        ]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        
        result = calculate_availability(
            weekly_schedule=weekly_schedule,
            date_exceptions=date_exceptions,
            busy_intervals=busy_intervals,
            start_date=start_date,
            end_date=end_date,
        )
        assert len(result) == 2
        assert result[0].end.hour == 10
        assert result[1].start.hour == 11

    def test_calculate_filters_past_times(self):
        """Test that past times are filtered out."""
        weekly_schedule = {
            0: [{"start": "09:00", "end": "12:00"}],  # Monday
        }
        date_exceptions = {}
        busy_intervals = []
        
        # Use a past date
        past_date = date.today() - timedelta(days=1)
        
        result = calculate_availability(
            weekly_schedule=weekly_schedule,
            date_exceptions=date_exceptions,
            busy_intervals=busy_intervals,
            start_date=past_date,
            end_date=past_date,
        )
        # All times should be filtered out as they're in the past
        assert all(tr.end > datetime.now(timezone.utc) for tr in result)

    def test_calculate_complex_scenario(self):
        """Test complex scenario with schedule, exceptions, and busy intervals."""
        weekly_schedule = {
            0: [{"start": "09:00", "end": "18:00"}],  # Monday
            1: [{"start": "09:00", "end": "18:00"}],  # Tuesday
        }
        date_exceptions = {
            date(2024, 1, 1): {"exception_type": "off"},  # Monday off
            date(2024, 1, 2): {  # Tuesday custom hours
                "exception_type": "custom",
                "custom_hours": [{"start": "10:00", "end": "14:00"}],
            },
        }
        busy_intervals = [
            TimeRange(
                start=datetime(2024, 1, 2, 11, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc),
            ),
        ]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        
        result = calculate_availability(
            weekly_schedule=weekly_schedule,
            date_exceptions=date_exceptions,
            busy_intervals=busy_intervals,
            start_date=start_date,
            end_date=end_date,
        )
        # Monday should be off, Tuesday should have custom hours minus busy interval
        # So we should have: 10:00-11:00 and 12:00-14:00
        tuesday_ranges = [r for r in result if r.start.date() == date(2024, 1, 2)]
        assert len(tuesday_ranges) == 2
        assert tuesday_ranges[0].start.hour == 10
        assert tuesday_ranges[0].end.hour == 11
        assert tuesday_ranges[1].start.hour == 12
        assert tuesday_ranges[1].end.hour == 14
