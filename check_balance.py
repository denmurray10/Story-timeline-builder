
import re

with open(r'c:\Users\denni\OneDrive\Documents\Vs projects\Story-timeline-builder\Story-timeline-builder-1\templates\timeline\base.html', 'r', encoding='utf-8') as f:
    content = f.read()

ifs = re.findall(r'\{%\s*if\s+', content)
endifs = re.findall(r'\{%\s*endif\s*%\}', content)

print(f"IFs: {len(ifs)}")
print(f"ENDIFs: {len(endifs)}")

# Check for unclosed ones line by line or nested
stack = []
for i, line in enumerate(content.splitlines(), 1):
    if '{% if ' in line:
        stack.append(i)
    if '{% endif %}' in line:
        if stack:
            stack.pop()
        else:
            print(f"Extra ENDIF at line {i}")

for line_num in stack:
    print(f"Unclosed IF from line {line_num}")
