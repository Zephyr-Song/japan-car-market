#!/usr/bin/env python3
"""Test script to diagnose the refresh_data.py issues"""
import sys, os
import traceback

print("=" * 50)
print("🔍 Diagnostic Test Start")
print("=" * 50)

# Test 1: Basic Python
print("\n✓ Test 1: Python is working")
print(f"Python version: {sys.version}")

# Test 2: Set encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
    print("\n✓ Test 2: Encoding set to UTF-8")
except Exception as e:
    print(f"\n✗ Test 2 Failed: {e}")

# Test 3: Add path
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    print(f"\n✓ Test 3: Added path: {script_dir}")
except Exception as e:
    print(f"\n✗ Test 3 Failed: {e}")

# Test 4: Import modules one by one
print("\n📦 Testing imports...")
try:
    print("  Importing update_crawler...", end=" ", flush=True)
    from update_crawler import crawl_incremental
    print("✓")
except Exception as e:
    print(f"✗ FAILED")
    traceback.print_exc()

try:
    print("  Importing process...", end=" ", flush=True)
    from process import process_data
    print("✓")
except Exception as e:
    print(f"✗ FAILED")
    traceback.print_exc()

try:
    print("  Importing macro_data_crawler...", end=" ", flush=True)
    from macro_data_crawler import refresh_macro_data
    print("✓")
except Exception as e:
    print(f"✗ FAILED")
    traceback.print_exc()

print("\n" + "=" * 50)
print("✅ Diagnostic Test Complete")
print("=" * 50)
