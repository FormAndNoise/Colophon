import os
import re

directory = r'H:\New folder\ComfyUI-MiniBook_Node\workflows'
files_to_patch = ['adapt_specialty_workflows.py', 'adapt_workflows.py']

for fname in files_to_patch:
    filepath = os.path.join(directory, fname)
    if not os.path.exists(filepath): continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace hardcoded font paths in workflows with 'default' so the new node logic picks it up
    content = content.replace('"C:/Windows/Fonts/georgia.ttf"', '"default"')
    content = content.replace('"C:/Windows/Fonts/arial.ttf"', '"default"')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Workflow patching complete!")
