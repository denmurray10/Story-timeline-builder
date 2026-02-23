import os
import re

directory = 'templates'

count = 0
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content = re.sub(r'\bcolours:\s*\{', 'colors: {', content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as out:
                    out.write(new_content)
                count += 1
                
print(f'Done reverting tailwind colours in {count} files.')
