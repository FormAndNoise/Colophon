"""
MiniBook Layout Compositor Node
================================
Takes the editorial plan from the Literary Editor, the generated illustrations,
and composes properly laid-out book pages with real typography, margins,
and intelligent text/image placement.
"""

from PIL import Image, ImageDraw, ImageFont
import torch
import numpy as np
import json
import re
import math


class MiniBookLayoutCompositor:
    """
    The Book Designer. Turns an editorial plan into composed page images
    with proper margins, typography, and text/image integration.
    """

    SHEET_SIZES = ["A4", "A5", "US_Letter", "US_Trade_6x9", "Square_8x8"]

    # Sheet dimensions in pixels at 300 DPI
    SHEET_DIMS = {
        "A4": (2480, 3508),
        "A5": (1748, 2480),
        "US_Letter": (2550, 3300),
        "US_Trade_6x9": (1800, 2700),
        "Square_8x8": (2400, 2400),
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "page_texts": ("STRING", {"forceInput": True}),
                "page_types": ("STRING", {"forceInput": True}),
                "sheet_size": (cls.SHEET_SIZES, {"default": "US_Trade_6x9"}),
                "font": ("STRING", {"default": "C:/Windows/Fonts/georgia.ttf"}),
                "body_font_size": ("INT", {"default": 42, "min": 16, "max": 120, "step": 1}),
                "title_font_size": ("INT", {"default": 72, "min": 24, "max": 200, "step": 1}),
                "margin_percent": ("FLOAT", {"default": 12.0, "min": 5.0, "max": 25.0, "step": 0.5}),
            },
            "optional": {
                "illustrations": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("composed_pages",)
    INPUT_IS_LIST = True
    FUNCTION = "compose"
    CATEGORY = "MiniBook"

    def _load_font(self, font_path, size):
        """Load a font with fallback to system default."""
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            try:
                return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
            except Exception:
                return ImageFont.load_default()

    def _wrap_text(self, text, font, max_width, draw):
        """Word-wrap text to fit within max_width pixels. Returns list of lines."""
        paragraphs = text.split('\n')
        lines = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                lines.append("")  # Preserve paragraph breaks
                continue

            words = paragraph.split()
            if not words:
                lines.append("")
                continue

            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                test_width = bbox[2] - bbox[0]

                if test_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

        return lines

    def _draw_drop_cap(self, draw, text, font_path, body_font, body_size, x, y, max_width, line_height):
        """
        Draw a drop cap for the first letter of the text.
        Returns (remaining_text, new_y) so the caller knows where to continue.
        """
        if not text or len(text) < 2:
            return text, y

        drop_letter = text[0]
        remaining = text[1:].lstrip()

        # Drop cap is 3x the body font size
        drop_size = body_size * 3
        drop_font = self._load_font(font_path, drop_size)

        # Measure drop cap
        drop_bbox = draw.textbbox((0, 0), drop_letter, font=drop_font)
        drop_width = drop_bbox[2] - drop_bbox[0]
        drop_height = drop_bbox[3] - drop_bbox[1]
        
        # Measure the small font to calculate the vertical alignment offset
        small_bbox = draw.textbbox((0, 0), remaining[:1] if remaining else "A", font=body_font)
        y_offset = drop_bbox[1] - small_bbox[1]

        # Draw the drop cap shifted UP by the calculated offset
        drop_color = (40, 40, 40)
        draw.text((x, y - y_offset), drop_letter, fill=drop_color, font=drop_font)

        # Wrap the remaining text around the drop cap for the first few lines
        drop_lines = max(1, drop_height // line_height)
        indent_width = drop_width + int(body_size * 0.5)

        lines = self._wrap_text(remaining, body_font, max_width - indent_width, draw)
        current_y = y

        # Draw indented lines (beside the drop cap)
        lines_drawn = 0
        for i, line in enumerate(lines):
            if i < drop_lines:
                draw.text((x + indent_width, current_y), line, fill=(30, 30, 30), font=body_font)
            else:
                break
            current_y += line_height
            lines_drawn += 1

        # Return remaining lines as rejoined text
        if lines_drawn < len(lines):
            remaining_text = '\n'.join(lines[lines_drawn:])
        else:
            remaining_text = ""

        return remaining_text, current_y

    def _compose_text_only(self, text, page_w, page_h, margins, font_path, body_size, line_height_factor=1.5):
        """Compose a text-only page with proper typography."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))  # Warm off-white
        draw = ImageDraw.Draw(page)

        body_font = self._load_font(font_path, body_size)
        line_height = int(body_size * line_height_factor)

        text_x = margins["left"]
        text_y = margins["top"]
        text_width = page_w - margins["left"] - margins["right"]
        text_height = page_h - margins["top"] - margins["bottom"]

        lines = self._wrap_text(text, body_font, text_width, draw)
        current_y = text_y

        for line in lines:
            if current_y + line_height > text_y + text_height:
                break  # Don't overflow the page
            if line == "":
                current_y += int(line_height * 0.6)  # Paragraph spacing
                continue
            draw.text((text_x, current_y), line, fill=(30, 30, 30), font=body_font)
            current_y += line_height

        return page

    def _compose_chapter_opener(self, text, page_w, page_h, margins, font_path, body_size, title_size):
        """Compose a chapter opener with decorative header and generous whitespace."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))
        draw = ImageDraw.Draw(page)

        title_font = self._load_font(font_path, title_size)
        body_font = self._load_font(font_path, body_size)
        line_height = int(body_size * 1.5)

        text_width = page_w - margins["left"] - margins["right"]

        # Extract chapter title if present (first line or "Chapter X" pattern)
        lines = text.strip().split('\n', 1)
        chapter_title = lines[0].strip()
        body_text = lines[1].strip() if len(lines) > 1 else ""

        # Position chapter title at ~30% down the page
        title_y = int(page_h * 0.30)

        # Draw a subtle decorative line above the title
        line_x_start = margins["left"] + int(text_width * 0.3)
        line_x_end = margins["left"] + int(text_width * 0.7)
        line_y = title_y - int(title_size * 0.8)
        draw.line([(line_x_start, line_y), (line_x_end, line_y)], fill=(160, 140, 120), width=2)

        # Draw chapter title centered
        title_bbox = draw.textbbox((0, 0), chapter_title, font=title_font)
        title_text_width = title_bbox[2] - title_bbox[0]
        title_x = margins["left"] + (text_width - title_text_width) // 2
        draw.text((title_x, title_y), chapter_title, fill=(40, 35, 30), font=title_font)

        # Draw decorative line below title
        below_y = title_y + title_size + int(title_size * 0.4)
        draw.line([(line_x_start, below_y), (line_x_end, below_y)], fill=(160, 140, 120), width=2)

        # Body text starts well below the title with a drop cap
        body_y = below_y + int(title_size * 1.2)

        if body_text:
            remaining, new_y = self._draw_drop_cap(
                draw, body_text, font_path, body_font, body_size,
                margins["left"], body_y, text_width, line_height
            )
            if remaining:
                remaining_lines = self._wrap_text(remaining, body_font, text_width, draw)
                for rline in remaining_lines:
                    if new_y + line_height > page_h - margins["bottom"]:
                        break
                    if rline == "":
                        new_y += int(line_height * 0.6)
                        continue
                    draw.text((margins["left"], new_y), rline, fill=(30, 30, 30), font=body_font)
                    new_y += line_height

        return page

    def _compose_text_with_illustration(self, text, illustration, page_w, page_h, margins, font_path, body_size):
        """Compose a page with text on one half and illustration on the other."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))
        draw = ImageDraw.Draw(page)

        body_font = self._load_font(font_path, body_size)
        line_height = int(body_size * 1.5)

        text_width = page_w - margins["left"] - margins["right"]

        if illustration is not None:
            # Top half: illustration
            illust_area_height = int((page_h - margins["top"] - margins["bottom"]) * 0.45)
            illust_y = margins["top"]

            # Resize illustration to fit
            illust_pil = illustration.resize(
                (text_width, illust_area_height), Image.LANCZOS
            )
            page.paste(illust_pil, (margins["left"], illust_y))

            # Bottom half: text
            text_y = illust_y + illust_area_height + int(body_size * 0.8)
        else:
            text_y = margins["top"]

        # Draw text
        lines = self._wrap_text(text, body_font, text_width, draw)
        current_y = text_y
        for line in lines:
            if current_y + line_height > page_h - margins["bottom"]:
                break
            if line == "":
                current_y += int(line_height * 0.6)
                continue
            draw.text((margins["left"], current_y), line, fill=(30, 30, 30), font=body_font)
            current_y += line_height

        return page

    def _compose_full_illustration(self, text, illustration, page_w, page_h, margins, font_path, body_size):
        """Compose a full-page illustration with optional caption."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))

        if illustration is not None:
            # Fill the page with the illustration (respecting margins)
            illust_w = page_w - margins["left"] - margins["right"]
            illust_h = page_h - margins["top"] - margins["bottom"]

            illust_pil = illustration.resize((illust_w, illust_h), Image.LANCZOS)
            page.paste(illust_pil, (margins["left"], margins["top"]))

        # Optional caption at the bottom
        if text and text.strip():
            draw = ImageDraw.Draw(page)
            
            # Use the book's font, scaled down slightly for the caption
            caption_size = max(16, int(body_size * 0.75))
            caption_font = self._load_font(font_path, caption_size)
            line_height = int(caption_size * 1.5)
            
            text_width = page_w - margins["left"] - margins["right"]
            lines = self._wrap_text(text.strip(), caption_font, text_width, draw)
            
            # Start drawing 20px below the illustration, inside the bottom margin
            caption_y = page_h - margins["bottom"] + 20
            
            for line in lines:
                # Prevent drawing off the bottom edge of the page
                if caption_y + line_height > page_h - 20:
                    break
                    
                line_bbox = draw.textbbox((0, 0), line, font=caption_font)
                line_w = line_bbox[2] - line_bbox[0]
                line_x = (page_w - line_w) // 2  # Center the caption
                
                draw.text((line_x, caption_y), line, fill=(100, 100, 100), font=caption_font)
                caption_y += line_height

        return page

    def _compose_section_break(self, text, page_w, page_h, margins, font_path, body_size):
        """Compose a section break page — minimal, elegant."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))
        draw = ImageDraw.Draw(page)

        # Center the text (if any) vertically on the page
        if text and text.strip():
            italic_size = int(body_size * 1.1)
            font = self._load_font(font_path, italic_size)
            text_width = page_w - margins["left"] - margins["right"]

            lines = self._wrap_text(text.strip(), font, text_width, draw)
            line_height = int(italic_size * 1.6)
            total_height = len(lines) * line_height

            start_y = (page_h - total_height) // 2

            for line in lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_w = line_bbox[2] - line_bbox[0]
                line_x = (page_w - line_w) // 2
                draw.text((line_x, start_y), line, fill=(80, 70, 60), font=font)
                start_y += line_height

        # Draw a centered ornamental divider
        divider_y = int(page_h * 0.48) if not text else start_y + line_height
        center_x = page_w // 2
        ornament = "— ✦ —"
        orn_font = self._load_font(font_path, int(body_size * 0.8))
        orn_bbox = draw.textbbox((0, 0), ornament, font=orn_font)
        orn_w = orn_bbox[2] - orn_bbox[0]
        draw.text((center_x - orn_w // 2, divider_y), ornament, fill=(140, 130, 110), font=orn_font)

        return page

    def compose(self, page_texts, page_types, sheet_size, font, body_font_size,
                title_font_size, margin_percent, illustrations=None):
        """Main execution: compose all pages according to the editorial plan."""

        # Unwrap list inputs (ComfyUI sends single values wrapped in lists when INPUT_IS_LIST=True)
        if isinstance(sheet_size, list):
            sheet_size = sheet_size[0]
        if isinstance(font, list):
            font = font[0]
        if isinstance(body_font_size, list):
            body_font_size = body_font_size[0]
        if isinstance(title_font_size, list):
            title_font_size = title_font_size[0]
        if isinstance(margin_percent, list):
            margin_percent = margin_percent[0]

        # Get page dimensions
        page_w, page_h = self.SHEET_DIMS.get(sheet_size, (1800, 2700))

        # Calculate margins
        margin_px_h = int(page_w * (margin_percent / 100.0))
        margin_px_v = int(page_h * (margin_percent / 100.0))
        margins = {
            "left": margin_px_h,
            "right": margin_px_h,
            "top": margin_px_v,
            "bottom": margin_px_v,
        }

        # Convert illustration tensors to PIL images if provided
        illust_pil_list = []
        if illustrations is not None:
            for illust_tensor in illustrations:
                if isinstance(illust_tensor, torch.Tensor):
                    np_img = illust_tensor.cpu().numpy()
                    if np_img.ndim == 4:
                        np_img = np_img.squeeze(0)
                    pil_img = Image.fromarray((np_img * 255).astype(np.uint8))
                    illust_pil_list.append(pil_img)

        # Compose each page
        composed_pages = []
        illust_idx = 0

        for i, (text, page_type) in enumerate(zip(page_texts, page_types)):
            # Determine if this page gets an illustration
            needs_illustration = page_type in ("text_with_illustration", "full_illustration")
            current_illust = None
            if needs_illustration and illust_idx < len(illust_pil_list):
                current_illust = illust_pil_list[illust_idx]
                illust_idx += 1

            # Compose based on page type
            if page_type == "chapter_opener":
                page_img = self._compose_chapter_opener(
                    text, page_w, page_h, margins, font, body_font_size, title_font_size
                )
            elif page_type == "text_with_illustration":
                page_img = self._compose_text_with_illustration(
                    text, current_illust, page_w, page_h, margins, font, body_font_size
                )
            elif page_type == "full_illustration":
                page_img = self._compose_full_illustration(
                    text, current_illust, page_w, page_h, margins, font, body_font_size
                )
            elif page_type == "section_break":
                page_img = self._compose_section_break(
                    text, page_w, page_h, margins, font, body_font_size
                )
            else:  # text_only or fallback
                page_img = self._compose_text_only(
                    text, page_w, page_h, margins, font, body_font_size
                )

            # Convert PIL to tensor
            page_tensor = torch.tensor(
                np.array(page_img).astype(np.float32) / 255.0
            ).unsqueeze(0)
            composed_pages.append(page_tensor)

        # Stack all page tensors into a single batch
        if composed_pages:
            result = torch.cat(composed_pages, dim=0)
        else:
            # Fallback: single blank page
            blank = Image.new('RGB', (page_w, page_h), (255, 255, 255))
            result = torch.tensor(np.array(blank).astype(np.float32) / 255.0).unsqueeze(0)

        return (result,)