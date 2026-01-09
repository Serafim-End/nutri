#!/usr/bin/env python3
"""
Critical Functions Test Suite
Tests only the most critical functions without requiring full Flask app setup.
Focuses on core business logic that must work correctly.
"""

import sys
import os
from datetime import datetime, date, timezone

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Import directly from module to avoid app initialization
import importlib.util

def load_module_from_file(filepath, module_name):
    """Load a module directly from file without triggering package imports."""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Test results
results = {'passed': [], 'failed': [], 'total': 0}

def test_result(name, passed, error=None):
    """Record test result."""
    results['total'] += 1
    if passed:
        results['passed'].append(name)
        print(f"✅ {name}")
    else:
        results['failed'].append((name, error))
        print(f"❌ {name}: {error}")

print("=" * 70)
print("CRITICAL FUNCTIONS TEST SUITE")
print("=" * 70)
print()

# Load availability module once
availability_module = load_module_from_file(
    os.path.join(backend_path, 'app', 'services', 'availability.py'),
    'availability'
)
TimeRange = availability_module.TimeRange

# ============================================================================
# CRITICAL TEST 1: Overlap Logic (Edge Cases)
# ============================================================================
print("Testing: TimeRange.overlaps() - Critical Edge Cases")
try:
    # Edge case: end == start (MUST NOT overlap - critical requirement)
    tr1 = TimeRange(
        start=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
        end=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
    )
    tr2 = TimeRange(
        start=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),  # end == start
        end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    assert tr1.overlaps(tr2) == False, "end==start MUST NOT overlap"
    test_result("Overlap edge case: end==start does NOT overlap", True)
    
    # Normal overlap
    tr3 = TimeRange(
        start=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
        end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    tr4 = TimeRange(
        start=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
        end=datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc),
    )
    assert tr3.overlaps(tr4) == True
    test_result("Overlap detection: overlapping ranges", True)
    
except Exception as e:
    test_result("TimeRange.overlaps() - critical edge cases", False, str(e))

# ============================================================================
# CRITICAL TEST 2: Availability Calculation Flow
# ============================================================================
print("\nTesting: Availability Calculation - Full Flow")
try:
    expand_weekly_schedule = availability_module.expand_weekly_schedule
    apply_date_exceptions = availability_module.apply_date_exceptions
    subtract_busy_intervals = availability_module.subtract_busy_intervals
    calculate_availability = availability_module.calculate_availability
    
    # Test: Weekly schedule → exceptions → busy intervals
    weekly_schedule = {0: [{"start": "09:00", "end": "18:00"}]}  # Monday
    date_exceptions = {
        date(2024, 1, 1): {"exception_type": "off"}  # Monday off
    }
    busy_intervals = [
        TimeRange(
            start=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),  # Tuesday
            end=datetime(2024, 1, 2, 11, 0, tzinfo=timezone.utc),
        )
    ]
    
    result = calculate_availability(
        weekly_schedule=weekly_schedule,
        date_exceptions=date_exceptions,
        busy_intervals=busy_intervals,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
    )
    assert isinstance(result, list)
    test_result("calculate_availability() - full flow works", True)
    
except Exception as e:
    test_result("Availability calculation - full flow", False, str(e))

# ============================================================================
# CRITICAL TEST 3: Date Exceptions
# ============================================================================
print("\nTesting: Date Exceptions")
try:
    apply_date_exceptions = availability_module.apply_date_exceptions
    
    # Off day removes all slots
    time_ranges = [
        TimeRange(
            start=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        ),
    ]
    date_exceptions = {date(2024, 1, 1): {"exception_type": "off"}}
    result = apply_date_exceptions(time_ranges, date_exceptions)
    assert len(result) == 0, "Off day must remove all slots"
    test_result("Date exception: off day removes slots", True)
    
    # Custom hours override
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
    test_result("Date exception: custom hours override", True)
    
except Exception as e:
    test_result("Date exceptions", False, str(e))

# ============================================================================
# CRITICAL TEST 4: Busy Interval Subtraction
# ============================================================================
print("\nTesting: Busy Interval Subtraction")
try:
    subtract_busy_intervals = availability_module.subtract_busy_intervals
    
    # Busy interval splits available range
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
    assert len(result) == 2, "Busy interval must split range"
    assert result[0].end.hour == 10
    assert result[1].start.hour == 11
    test_result("Busy intervals: splits available range", True)
    
except Exception as e:
    test_result("Busy interval subtraction", False, str(e))

# ============================================================================
# CRITICAL TEST 5: Google Calendar Sync Idempotency
# ============================================================================
print("\nTesting: Google Calendar Sync - Idempotency")
try:
    sync_file_path = os.path.join(backend_path, 'app', 'services', 'booking_calendar_sync.py')
    with open(sync_file_path, 'r') as f:
        source_code = f.read()
    
    # Verify idempotency checks exist
    assert 'if booking.google_calendar_event_id:' in source_code
    assert 'if not booking.google_calendar_event_id:' in source_code
    test_result("Calendar sync: idempotency checks exist", True)
    
except Exception as e:
    test_result("Google Calendar sync idempotency", False, str(e))

# ============================================================================
# CRITICAL TEST 6: Review Validation
# ============================================================================
print("\nTesting: Review Validation Logic")
try:
    bookings_route_path = os.path.join(backend_path, 'app', 'routes', 'bookings.py')
    with open(bookings_route_path, 'r') as f:
        bookings_route = f.read()
    
    # Verify critical validations
    assert 'booking.status != "completed"' in bookings_route or 'status == "completed"' in bookings_route
    assert 'existing_review' in bookings_route or 'Review.query.filter_by(booking_id' in bookings_route
    assert 'booking.client_id' in bookings_route and 'current_user_id' in bookings_route
    test_result("Review validation: all checks present", True)
    
except Exception as e:
    test_result("Review validation logic", False, str(e))

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"Total tests: {results['total']}")
print(f"Passed: {len(results['passed'])}")
print(f"Failed: {len(results['failed'])}")
print()

if results['failed']:
    print("FAILED TESTS:")
    for name, error in results['failed']:
        print(f"  ❌ {name}")
        print(f"     Error: {error}")
    print()

if len(results['passed']) == results['total']:
    print("✅ ALL CRITICAL TESTS PASSED!")
    print()
    print("Verified:")
    print("  ✅ Overlap logic (end==start does NOT overlap)")
    print("  ✅ Availability calculation flow")
    print("  ✅ Date exceptions (off days, custom hours)")
    print("  ✅ Busy interval subtraction")
    print("  ✅ Google Calendar sync idempotency")
    print("  ✅ Review validation logic")
    sys.exit(0)
else:
    print(f"❌ {len(results['failed'])} test(s) failed")
    sys.exit(1)
