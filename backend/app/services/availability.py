"""
Availability Calculation Service
Pure functions for calculating available time slots from working hours,
date exceptions, and Google Calendar busy intervals.
"""

from datetime import datetime, date, time, timedelta, timezone
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class TimeRange:
    """Represents a time range with start and end times."""
    start: datetime
    end: datetime

    def __post_init__(self):
        """Ensure timezone-aware datetimes."""
        if self.start.tzinfo is None:
            self.start = self.start.replace(tzinfo=timezone.utc)
        if self.end.tzinfo is None:
            self.end = self.end.replace(tzinfo=timezone.utc)

    def overlaps(self, other: 'TimeRange') -> bool:
        """Check if this time range overlaps with another."""
        return self.start < other.end and self.end > other.start

    def contains(self, other: 'TimeRange') -> bool:
        """Check if this time range fully contains another."""
        return self.start <= other.start and self.end >= other.end


def expand_weekly_schedule(
    weekly_schedule: Dict[int, List[Dict[str, str]]],
    start_date: date,
    end_date: date,
) -> List[TimeRange]:
    """
    Expand weekly schedule to specific date ranges.
    
    Args:
        weekly_schedule: Dict mapping weekday (0=Monday, 6=Sunday) to list of time ranges
                         Each time range is {"start": "HH:MM", "end": "HH:MM"}
        start_date: First date to generate slots for
        end_date: Last date to generate slots for (inclusive)
    
    Returns:
        List of TimeRange objects for all working hours in the date range
    """
    time_ranges = []
    current_date = start_date
    
    while current_date <= end_date:
        weekday = current_date.weekday()  # 0=Monday, 6=Sunday
        day_schedule = weekly_schedule.get(weekday, [])
        
        for time_slot in day_schedule:
            start_time_str = time_slot.get("start", "")
            end_time_str = time_slot.get("end", "")
            
            if not start_time_str or not end_time_str:
                continue
            
            try:
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
                
                # Combine date and time, make timezone-aware
                start_dt = datetime.combine(current_date, start_time).replace(tzinfo=timezone.utc)
                end_dt = datetime.combine(current_date, end_time).replace(tzinfo=timezone.utc)
                
                # Handle case where end time is next day (e.g., 22:00-02:00)
                if end_time < start_time:
                    end_dt += timedelta(days=1)
                
                time_ranges.append(TimeRange(start=start_dt, end=end_dt))
            except ValueError:
                # Skip invalid time format
                continue
        
        current_date += timedelta(days=1)
    
    return time_ranges


def apply_date_exceptions(
    time_ranges: List[TimeRange],
    date_exceptions: Dict[date, Dict[str, Any]],
) -> List[TimeRange]:
    """
    Apply date exceptions to time ranges.
    
    Args:
        time_ranges: List of TimeRange objects from weekly schedule
        date_exceptions: Dict mapping date to exception data
                        {"exception_type": "off"|"custom", "custom_hours": [...]}
    
    Returns:
        List of TimeRange objects with exceptions applied
    """
    # Group time ranges by date
    ranges_by_date: Dict[date, List[TimeRange]] = {}
    for tr in time_ranges:
        tr_date = tr.start.date()
        if tr_date not in ranges_by_date:
            ranges_by_date[tr_date] = []
        ranges_by_date[tr_date].append(tr)
    
    result = []
    
    for tr_date, ranges in ranges_by_date.items():
        if tr_date in date_exceptions:
            exception = date_exceptions[tr_date]
            exception_type = exception.get("exception_type")
            
            if exception_type == "off":
                # Skip all ranges for this date
                continue
            elif exception_type == "custom":
                # Replace with custom hours
                custom_hours = exception.get("custom_hours", [])
                for time_slot in custom_hours:
                    start_time_str = time_slot.get("start", "")
                    end_time_str = time_slot.get("end", "")
                    
                    if not start_time_str or not end_time_str:
                        continue
                    
                    try:
                        start_time = datetime.strptime(start_time_str, "%H:%M").time()
                        end_time = datetime.strptime(end_time_str, "%H:%M").time()
                        
                        start_dt = datetime.combine(tr_date, start_time).replace(tzinfo=timezone.utc)
                        end_dt = datetime.combine(tr_date, end_time).replace(tzinfo=timezone.utc)
                        
                        if end_time < start_time:
                            end_dt += timedelta(days=1)
                        
                        result.append(TimeRange(start=start_dt, end=end_dt))
                    except ValueError:
                        continue
            else:
                # Unknown exception type, keep original ranges
                result.extend(ranges)
        else:
            # No exception for this date, keep original ranges
            result.extend(ranges)
    
    return result


def subtract_busy_intervals(
    time_ranges: List[TimeRange],
    busy_intervals: List[TimeRange],
) -> List[TimeRange]:
    """
    Subtract busy intervals from available time ranges.
    
    Args:
        time_ranges: List of available TimeRange objects
        busy_intervals: List of busy TimeRange objects to subtract
    
    Returns:
        List of TimeRange objects with busy intervals removed
    """
    if not busy_intervals:
        return time_ranges
    
    result = []
    
    for available_range in time_ranges:
        # Start with the full available range
        remaining_ranges = [available_range]
        
        # Subtract each busy interval
        for busy_range in busy_intervals:
            if not available_range.overlaps(busy_range):
                continue
            
            new_remaining = []
            for remaining in remaining_ranges:
                if not remaining.overlaps(busy_range):
                    # No overlap, keep as is
                    new_remaining.append(remaining)
                elif busy_range.contains(remaining):
                    # Busy interval fully contains this range, remove it
                    continue
                elif remaining.contains(busy_range):
                    # Available range fully contains busy interval, split it
                    # Create range before busy interval
                    if remaining.start < busy_range.start:
                        new_remaining.append(TimeRange(
                            start=remaining.start,
                            end=busy_range.start
                        ))
                    # Create range after busy interval
                    if busy_range.end < remaining.end:
                        new_remaining.append(TimeRange(
                            start=busy_range.end,
                            end=remaining.end
                        ))
                else:
                    # Partial overlap, trim the available range
                    if remaining.start < busy_range.start:
                        # Busy interval starts after available range
                        new_remaining.append(TimeRange(
                            start=remaining.start,
                            end=busy_range.start
                        ))
                    elif busy_range.end < remaining.end:
                        # Busy interval ends before available range
                        new_remaining.append(TimeRange(
                            start=busy_range.end,
                            end=remaining.end
                        ))
                    # Otherwise, the range is fully covered
            
            remaining_ranges = new_remaining
        
        result.extend(remaining_ranges)
    
    # Sort by start time
    result.sort(key=lambda tr: tr.start)
    return result


def parse_google_calendar_busy(
    freebusy_result: Dict[str, Any],
    calendar_id: Optional[str] = None,
) -> List[TimeRange]:
    """
    Parse Google Calendar freebusy result into TimeRange objects.
    
    Args:
        freebusy_result: Result from Google Calendar freebusy API
        calendar_id: Optional calendar ID to extract (if None, uses first calendar)
    
    Returns:
        List of TimeRange objects representing busy intervals
    """
    busy_intervals = []
    
    calendars = freebusy_result.get("calendars", {})
    
    # If calendar_id specified, use that; otherwise use first calendar
    if calendar_id and calendar_id in calendars:
        calendar_data = calendars[calendar_id]
    elif calendars:
        # Use first calendar
        calendar_data = next(iter(calendars.values()))
    else:
        return busy_intervals
    
    busy_periods = calendar_data.get("busy", [])
    
    for period in busy_periods:
        start_str = period.get("start")
        end_str = period.get("end")
        
        if not start_str or not end_str:
            continue
        
        try:
            # Parse ISO format datetime strings
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            
            # Ensure timezone-aware
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            
            busy_intervals.append(TimeRange(start=start_dt, end=end_dt))
        except (ValueError, AttributeError):
            # Skip invalid datetime format
            continue
    
    return busy_intervals


def calculate_availability(
    weekly_schedule: Dict[int, List[Dict[str, str]]],
    date_exceptions: Dict[date, Dict[str, Any]],
    busy_intervals: List[TimeRange],
    start_date: date,
    end_date: date,
) -> List[TimeRange]:
    """
    Calculate available time slots from working hours, exceptions, and busy intervals.
    
    This is the main function that combines all steps:
    1. Expand weekly schedule to date range
    2. Apply date exceptions
    3. Subtract busy intervals
    
    Args:
        weekly_schedule: Dict mapping weekday (0=Monday, 6=Sunday) to list of time ranges
        date_exceptions: Dict mapping date to exception data
        busy_intervals: List of TimeRange objects representing busy times
        start_date: First date to calculate availability for
        end_date: Last date to calculate availability for (inclusive)
    
    Returns:
        List of TimeRange objects representing available time slots
    """
    # Step 1: Expand weekly schedule
    time_ranges = expand_weekly_schedule(weekly_schedule, start_date, end_date)
    
    # Step 2: Apply date exceptions
    time_ranges = apply_date_exceptions(time_ranges, date_exceptions)
    
    # Step 3: Subtract busy intervals
    time_ranges = subtract_busy_intervals(time_ranges, busy_intervals)
    
    # Filter out past times and ensure all ranges are in the requested date range
    now = datetime.now(timezone.utc)
    result = []
    for tr in time_ranges:
        # Only include future times
        if tr.end <= now:
            continue
        # Only include times within the requested date range
        if tr.start.date() < start_date or tr.start.date() > end_date:
            continue
        result.append(tr)
    
    return result
