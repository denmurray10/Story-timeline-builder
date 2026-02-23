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

            new_content = content
            
            # revert all "colour" inside <style> tags
            def revert_style(match):
                text = match.group(0)
                return text.replace('colour', 'color').replace('Colour', 'Color')
            new_content = re.sub(r'<style.*?>.*?</style>', revert_style, new_content, flags=re.DOTALL|re.IGNORECASE)
            
            # CSS variables and standard properties that got hit incorrectly
            new_content = re.sub(r'([a-z0-9-]*)-colour\b', r'\1-color', new_content)
            new_content = re.sub(r'\bcolour:\s*([^;]+);', r'color: \1;', new_content)
            
            # Revert colour inside Django template tags {{ ... }} and {% ... %}
            def revert_django(match):
                 return match.group(0).replace('colour', 'color').replace('Colour', 'Color')
            new_content = re.sub(r'\{\{.*?\}\}', revert_django, new_content)
            new_content = re.sub(r'\{%.*?%\}', revert_django, new_content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as out:
                    out.write(new_content)
                count += 1
                
print(f'Done reverting in {count} files.')
