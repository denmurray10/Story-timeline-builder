
filename = r"c:\Users\denni\OneDrive\Documents\Vs projects\Story-timeline-builder\Story-timeline-builder-1\templates\timeline\landingpagev2.html"
with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()

subset = lines[482:1104] # 0-indexed, line 483 to 1104
content = "".join(subset)

import re
openings = re.findall(r'<div\b', content)
closings = re.findall(r'</div>', content)

print(f"Openings: {len(openings)}")
print(f"Closings: {len(closings)}")

# Find imbalance areas
stack = []
for i, line in enumerate(subset):
    ln = i + 483
    for m in re.finditer(r'<div\b|</div>', line):
        if m.group() == '<div':
            stack.append(ln)
        else:
            if stack:
                stack.pop()
            else:
                print(f"Unmatched closing at line {ln}")

print(f"Unclosed openings from lines: {stack}")
