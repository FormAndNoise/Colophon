import os
import re

filepath = r'H:\New folder\ComfyUI-MiniBook_Node\nodes\layout_compositor.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add TARGET_IMAGE_SIZES right after SHEET_DIMS
target_sizes = '''
    # Hardcoded (width, height) bounds for images on each sheet format
    # Format: (Half-page image size, Full-page image size)
    TARGET_IMAGE_SIZES = {
        "A4": ((1800, 1200), (1800, 2400)),
        "A5": ((1200, 800), (1200, 1600)),
        "US_Letter": ((1850, 1250), (1850, 2300)),
        "US_Trade_6x9": ((1400, 950), (1400, 1900)),
        "Square_8x8": ((1600, 900), (1600, 1600)),
    }
'''
if 'TARGET_IMAGE_SIZES =' not in content:
    content = content.replace('    SHEET_DIMS = {', target_sizes.lstrip('\n') + '    SHEET_DIMS = {')

# Change function signatures
content = content.replace('def _compose_text_with_illustration(self, text, illustration, page_w, page_h, margins, font_path, body_size):', 'def _compose_text_with_illustration(self, text, illustration, page_w, page_h, margins, font_path, body_size, sheet_size):')
content = content.replace('def _compose_full_illustration(self, text, illustration, page_w, page_h, margins, font_path, body_size):', 'def _compose_full_illustration(self, text, illustration, page_w, page_h, margins, font_path, body_size, sheet_size):')

# Update compose() calls
content = content.replace('self._compose_text_with_illustration(\n                    text, current_illust, page_w, page_h, margins, font, body_font_size\n                )', 'self._compose_text_with_illustration(\n                    text, current_illust, page_w, page_h, margins, font, body_font_size, sheet_size\n                )')
content = content.replace('self._compose_full_illustration(\n                    text, current_illust, page_w, page_h, margins, font, body_font_size\n                )', 'self._compose_full_illustration(\n                    text, current_illust, page_w, page_h, margins, font, body_font_size, sheet_size\n                )')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
