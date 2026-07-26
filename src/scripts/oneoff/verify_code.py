import re

with open('src/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find st.tabs block
start = content.find('st.tabs([')
if start != -1:
    end = content.find('])', start)
    tab_block = content[start:end+2]
    tab_names = re.findall(r'"([^"]+)"', tab_block)
    print(f"Tab count: {len(tab_names)}")
    for i, name in enumerate(tab_names):
        print(f'  {i}: {name.encode("ascii", "replace").decode()}')
else:
    print("st.tabs not found")

# Also check for the 'New Car Export by Destination Region' text
if "New Car Export by Destination Region" in content:
    print("\n'New Car Export by Destination Region' found in code")
else:
    print("\n'New Car Export by Destination Region' NOT found!")

# Check for remaining Chinese in UI strings
lines = content.split('\n')
cn_lines = []
for i, line in enumerate(lines, 1):
    # Check for Chinese/Japanese chars in st.markdown, st.metric, st.tabs strings
    if re.search(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]', line):
        if any(kw in line for kw in ['st.markdown', 'st.metric', 'st.tabs', 'st.warning', 'st.caption']):
            cn_lines.append((i, line.strip()))
print(f"\nLines with CJK in UI calls: {len(cn_lines)}")
for ln, txt in cn_lines[:15]:
    print(f"  L{ln}: {txt[:80]}")
