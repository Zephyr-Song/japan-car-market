"""Patch dashboard.py - find and fix"""

path = r"D:\japan-car-market\src\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find chart_domestic_vs_import(df)
for i, line in enumerate(lines):
    if "chart_domestic_vs_import" in line and "def " not in line:
        print(f"Line {i+1}: {line.rstrip()[:80]}")
        # Print 10 lines after
        for j in range(i+1, min(i+10, len(lines))):
            print(f"  {j+1}: {lines[j].rstrip()[:80]}")
        break
