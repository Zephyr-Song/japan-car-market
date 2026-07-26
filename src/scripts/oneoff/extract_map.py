import ast

with open('src/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find region_map = { ... }
start = content.find('region_map = {')
if start == -1:
    print("region_map not found!")
    exit()

brace_count = 0
end = start
for i, c in enumerate(content[start:], start):
    if c == '{':
        brace_count += 1
    elif c == '}':
        brace_count -= 1
        if brace_count == 0:
            end = i + 1
            break

dict_code = content[start:end]

# Extract the dict using exec
namespace = {}
exec(dict_code, namespace)
region_map = namespace['region_map']

print(f"Keys in region_map: {len(region_map)}")
for k, v in region_map.items():
    print(f"  {repr(k)} ({[hex(ord(c)) for c in k]}) -> {v}")

# Test against DB values
test_values = ['北美', '中近东', '中南美', '欧州', '亚洲', '非洲', '大洋州', '合计']
print("\nDB value lookup:")
for v in test_values:
    result = region_map.get(v, '*** NOT FOUND ***')
    print(f"  {repr(v)} ({[hex(ord(c)) for c in v]}) -> {result}")
