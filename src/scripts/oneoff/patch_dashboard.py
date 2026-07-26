"""Patch dashboard.py - insert tab11/tab12 at exact line numbers"""

path = r"D:\japan-car-market\src\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Line 1513 (0-indexed 1512) = "        chart_domestic_vs_import(df)\n"
# Line 1514 (0-indexed 1513) = "\n"
# Line 1515 (0-indexed 1514) = '    st.markdown("""\n'
# We insert before line 1515 (0-indexed 1514)

insert_idx = 1514  # 0-indexed

# Verify
assert "st.markdown" in lines[insert_idx], f"Expected st.markdown at line {insert_idx+1}, got: {repr(lines[insert_idx])}"

new_lines = [
    "    with tab11:\n",
    '        st.markdown(\'<div class="section-title">Japan Used Car Export Statistics</div>\', unsafe_allow_html=True)\n',
    "        chart_export_statistics()\n",
    "\n",
    "    with tab12:\n",
    '        st.markdown(\'<div class="section-title">Monthly Market Report \u2014 Registration & Rankings</div>\', unsafe_allow_html=True)\n',
    "        chart_market_report()\n",
    "\n",
]

lines = lines[:insert_idx] + new_lines + lines[insert_idx:]

# Fix footer text
for i in range(len(lines)):
    if "10 Tabs:" in lines[i]:
        lines[i] = lines[i].replace("10 Tabs:", "12 Tabs:")
        lines[i] = lines[i].replace(
            "Domestic vs Import\n",
            "Domestic vs Import \u00b7 Export Stats \u00b7 Market Report\n"
        )
    if "carsensor.net + JADA" in lines[i] and "jumv.net" not in lines[i]:
        lines[i] = lines[i].replace(
            "\u5168\u8efd\u81ea\u5354 \u00b7",
            "\u5168\u8efd\u81ea\u5354 + jumv.net + \u8eca\u9078\u3073\u30c9\u30c3\u30c8\u30b3\u30e0 \u00b7"
        )

with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("OK: dashboard.py patched")
