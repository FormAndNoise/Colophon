import os
import re

directory = r'H:\New folder\ComfyUI-MiniBook_Node\nodes'
files_to_patch = ['core_controls.py', 'front_matter.py', 'layout_compositor.py']

for fname in files_to_patch:
    filepath = os.path.join(directory, fname)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add the import if not there
    if 'from .font_utils' not in content:
        content = content.replace('import numpy as np', 'import numpy as np\nfrom .font_utils import get_available_fonts, get_font_path')

    # Replace ComfyUI node input definitions
    content = re.sub(r'"font": \("STRING", \{"default": "C:/Windows/Fonts/[^"]+\.ttf"\}\),',
                     r'"font": (get_available_fonts(), ),', content)

    # Replace ImageFont.truetype calls
    # Usually it's: ImageFont.truetype(font_path, ...) or ImageFont.truetype(font, ...)
    # But wait, in core_controls.py:
    # "fallback_font = \"C:/Windows/Fonts/arial.ttf\""
    content = content.replace('fallback_font = "C:/Windows/Fonts/arial.ttf"', 'fallback_font = get_font_path("default")')
    content = content.replace('ImageFont.truetype("C:/Windows/Fonts/arial.ttf"', 'ImageFont.truetype(get_font_path("default")')

    # Replace usages where variables are passed
    # like: font = ImageFont.truetype(font_path, font_size)
    content = re.sub(r'ImageFont\.truetype\((font_path|font),', r'ImageFont.truetype(get_font_path(\1),', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Patching complete!")
