#!/usr/bin/env python3
"""
Unit tests for time formatting functionality in the journal writing timer feature.
"""

from django.test import TestCase
from authentication.templatetags.time_filters import format_writing_time


class TestTimeFormatting(TestCase):
    """Test cases for the time formatting functionality."""
    
    def test_zero_seconds(self):
        """Test formatting when writing time is 0 seconds."""
        result = format_writing_time(0)
        self.assertEqual(result, "N/A")
    
    def test_none_value(self):
        """Test formatting when writing time is None."""
        result = format_writing_time(None)
        self.assertEqual(result, "N/A")
    
    def test_empty_string(self):
        """Test formatting when writing time is an empty string."""
        result = format_writing_time("")
        self.assertEqual(result, "N/A")
    
    def test_less_than_one_minute(self):
        """Test formatting for times less than 60 seconds."""
        test_cases = [
            (1, "1s"),
            (30, "30s"),
            (45, "45s"),
            (59, "59s")
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_writing_time(seconds)
                self.assertEqual(result, expected, f"Expected {expected} for {seconds} seconds, got {result}")
    
    def test_one_to_fifty_nine_minutes(self):
        """Test formatting for times between 1 minute and 59 minutes."""
        test_cases = [
            (60, "1m"),      # Exactly 1 minute
            (90, "1m"),      # 1 minute 30 seconds
            (120, "2m"),     # Exactly 2 minutes
            (1800, "30m"),   # 30 minutes
            (3540, "59m"),   # 59 minutes
            (3599, "59m")    # 59 minutes 59 seconds
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_writing_time(seconds)
                self.assertEqual(result, expected, f"Expected {expected} for {seconds} seconds, got {result}")
    
    def test_one_hour_and_above(self):
        """Test formatting for times of 1 hour or more."""
        test_cases = [
            (3600, "1.0h"),      # Exactly 1 hour
            (3660, "1.0h"),      # 1 hour 1 minute
            (5400, "1.5h"),      # 1 hour 30 minutes
            (7200, "2.0h"),      # Exactly 2 hours
            (10800, "3.0h"),     # 3 hours
            (3661, "1.0h"),      # 1 hour 1 second
            (7201, "2.0h"),      # 2 hours 1 second
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_writing_time(seconds)
                self.assertEqual(result, expected, f"Expected {expected} for {seconds} seconds, got {result}")
    
    def test_string_input_conversion(self):
        """Test that string inputs are properly converted to integers."""
        test_cases = [
            ("30", "30s"),
            ("120", "2m"),
            ("3600", "1.0h"),
            ("0", "N/A")
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_writing_time(seconds)
                self.assertEqual(result, expected, f"Expected {expected} for '{seconds}', got {result}")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        test_cases = [
            (59, "59s"),     # Just under 1 minute
            (60, "1m"),      # Exactly 1 minute
            (61, "1m"),      # Just over 1 minute
            (3599, "59m"),   # Just under 1 hour
            (3600, "1.0h"),  # Exactly 1 hour
            (3601, "1.0h"),  # Just over 1 hour
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_writing_time(seconds)
                self.assertEqual(result, expected, f"Expected {expected} for {seconds} seconds, got {result}")
    
    def test_large_values(self):
        """Test formatting for very large time values."""
        test_cases = [
            (86400, "24.0h"),    # 24 hours
            (172800, "48.0h"),   # 48 hours
            (259200, "72.0h"),   # 72 hours
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_writing_time(seconds)
                self.assertEqual(result, expected, f"Expected {expected} for {seconds} seconds, got {result}")
    
    def test_negative_values(self):
        """Test that negative values are handled gracefully."""
        result = format_writing_time(-30)
        self.assertEqual(result, "-30s")
    
    def test_float_values(self):
        """Test that float values are properly converted."""
        test_cases = [
            (30.5, "30s"),
            (60.7, "1m"),
            (3600.2, "1.0h"),
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_writing_time(seconds)
                self.assertEqual(result, expected, f"Expected {expected} for {seconds} seconds, got {result}")


class TestTimeFormattingIntegration(TestCase):
    """Integration tests for time formatting in real-world scenarios."""
    
    def test_journal_writing_scenarios(self):
        """Test realistic journal writing time scenarios."""
        scenarios = [
            (45, "45s", "Quick journal entry"),
            (120, "2m", "Short reflection"),
            (600, "10m", "Medium journal entry"),
            (1800, "30m", "Detailed reflection"),
            (3600, "1.0h", "Long journal session"),
            (5400, "1.5h", "Extended writing session"),
        ]
        
        for seconds, expected_format, description in scenarios:
            with self.subTest(description=description):
                result = format_writing_time(seconds)
                self.assertEqual(result, expected_format, f"Failed for {description}: expected {expected_format}, got {result}")
    
    def test_format_consistency(self):
        """Test that the same input always produces the same output."""
        test_values = [30, 120, 3600, 7200]
        
        for value in test_values:
            with self.subTest(value=value):
                result1 = format_writing_time(value)
                result2 = format_writing_time(value)
                result3 = format_writing_time(value)
                
                self.assertEqual(result1, result2, f"Inconsistent results for {value}: {result1} != {result2}")
                self.assertEqual(result2, result3, f"Inconsistent results for {value}: {result2} != {result3}")
                self.assertEqual(result1, result3, f"Inconsistent results for {value}: {result1} != {result3}")
    
    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        invalid_inputs = [
            "invalid",
            "abc123",
            "12.34.56",
            None,
            "",
            "0",
            0
        ]
        
        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                result = format_writing_time(invalid_input)
                # All invalid inputs should return "N/A" except for 0 and "0"
                if invalid_input in [None, "", "invalid", "abc123", "12.34.56"]:
                    self.assertEqual(result, "N/A", f"Expected 'N/A' for {invalid_input}, got {result}")
                elif invalid_input in [0, "0"]:
                    self.assertEqual(result, "N/A", f"Expected 'N/A' for {invalid_input}, got {result}") 