import re

with open('D:/japan-car-market/src/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all lines with CJK or Japanese-specific characters
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if any(0x3000 <= ord(c) <= 0x9FFF or 0x30A0 <= ord(c) <= 0x30FF for c in line):
        # Write to file to avoid encoding issues
        with open('D:/japan-car-market/src/jp_lines.txt', 'a', encoding='utf-8') as out:
            out.write(f'L{i}: {line[:150]}\n')

print("Done - check jp_lines.txt")
