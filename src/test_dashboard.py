import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.chdir(r'D:\japan-car-market')
exec(open('src/dashboard.py', encoding='utf-8').read().split('def main()')[0])
print("Dashboard functions loaded OK")

# Test chart_import_export function exists
if 'chart_import_export' in dir():
    print("chart_import_export function found")
else:
    print("ERROR: chart_import_export not found")
