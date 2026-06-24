#!/usr/bin/env python3
"""
One-click data refresh: crawl new listings + reprocess + print summary
Run this on a schedule (e.g. every 30 min) to keep data fresh
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_crawler import crawl_incremental
from process import process_data
from macro_data_crawler import refresh_macro_data

def refresh():
    print("=" * 50)
    print("🔄 Data Refresh Start")
    print("=" * 50)
    new_count = crawl_incremental()
    if new_count > 0:
        print(f"\n📊 Reprocessing {new_count} new records...")
        process_data()
    else:
        print("\n📭 No new vehicles found, data is up to date")

    # 宏观数据刷新 (JADA + K-car + MarkLines)
    try:
        refresh_macro_data()
    except Exception as e:
        print(f"\n⚠ Macro data refresh failed: {e}")
    
    ts_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', '.last_refresh')
    print(f"\n✅ Refresh complete. Next refresh recommended in 30 min.")

if __name__ == "__main__":
    refresh()
