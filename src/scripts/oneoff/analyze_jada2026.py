"""分析 2026 年 JADA Excel 格式"""
import sys, os, tempfile, re
import requests
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja,en;q=0.9"}
TIMEOUT = 60

url = "https://www.jada.or.jp/files/libs/7209/20260603154913819.xls"
resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
fd, path = tempfile.mkstemp(suffix=".xls")
with os.fdopen(fd, "wb") as f:
    f.write(resp.content)

xl = pd.ExcelFile(path, engine="xlrd")
print(f"Sheets: {xl.sheet_names}")

df = pd.read_excel(xl, sheet_name="2026年5月", header=None)
print(f"Shape: {df.shape}")

# 打印所有行
for i in range(min(30, len(df))):
    row_vals = []
    for j in range(min(16, df.shape[1])):
        v = df.iloc[i, j]
        if pd.notna(v):
            row_vals.append(f"[{j}]={v}")
    if row_vals:
        print(f"Row {i}: {' '.join(row_vals)}")

os.unlink(path)
