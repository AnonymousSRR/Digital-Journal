#!/usr/bin/env python
"""
Utility script to list recent test logs
"""
import os
import glob
from pathlib import Path
from datetime import datetime

def list_recent_test_logs(limit=10):
    """List the most recent test log files"""
    
    test_logs_dir = Path("test_logs")
    
    if not test_logs_dir.exists():
        print("❌ test_logs directory not found!")
        return
    
    # Get all test log files
    log_files = list(test_logs_dir.glob("test_log_*.txt"))
    
    if not log_files:
        print("📁 No test log files found in test_logs/")
        return
    
    # Sort by modification time (newest first)
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print("📋 RECENT TEST LOGS")
    print("=" * 80)
    print(f"Found {len(log_files)} log files")
    print("=" * 80)
    
    for i, log_file in enumerate(log_files[:limit]):
        # Get file stats
        stat = log_file.stat()
        size_kb = stat.st_size / 1024
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        
        # Try to extract test results from the file
        test_results = "Unknown"
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                if "Ran 101 tests" in content:
                    test_results = "✅ 101/101 tests passed"
                elif "FAILED" in content:
                    test_results = "❌ Some tests failed"
                elif "ERROR" in content:
                    test_results = "💥 Test errors occurred"
        except:
            test_results = "📄 Log file"
        
        print(f"{i+1:2d}. {log_file.name}")
        print(f"    📅 {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    📊 {test_results}")
        print(f"    💾 {size_kb:.1f} KB")
        print()

if __name__ == '__main__':
    list_recent_test_logs() 