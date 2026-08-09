"""
MiniBook Front Matter Generator Node
=====================================
Generates the pages that make a PDF feel like a real book: title page,
copyright, dedication, table of contents, author bio, and back cover blurb.
Uses an LLM for contextually appropriate creative content.
"""

import os

from PIL import Image, ImageDraw, ImageFont
import torch
import numpy as np
import json
from .llm_bridge import run_llm

# Bundled fonts ship with the pack; use them as a portable fallback so pages
# render with a real TTF even when the user-configured font path is missing.
_BUNDLED_FONT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts"
)


class MiniBookFrontMatter:
    """
    The Publisher. Generates front and back matter pages that transform
    a collection of pages into something that feels like an actual book.
    """

    SHEET_SIZES = ["A4", "A5", "US_Letter", "US_Trade_6x9", "Square_8x8"]

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
                "editorial_plan": ("STRING", {"multiline": True, "forceInput": True}),
                "raw_story": ("STRING", {"multiline": True, "forceInput": True}),
                "author_name": ("STRING", {"default": "A MiniBook Original", "multiline": False}),
                "sheet_size": (cls.SHEET_SIZES, {"default": "US_Trade_6x9"}),
                "font": ("STRING", {"default": "C:/Windows/Fonts/georgia.ttf"}),
                "context": ("LLM_CONTEXT",),
            },
            "optional": {
                "include_dedication": ("BOOLEAN", {"default": True}),
                "include_toc": ("BOOLEAN", {"default": True}),
                "include_author_bio": ("BOOLEAN", {"default": True}),
                "include_back_blurb": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("front_pages", "back_pages")
    FUNCTION = "generate"
    CATEGORY = "MiniBook"

    def _load_font(self, font_path, size):
        """Load a font with fallback to bundled fonts, then system default."""
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
        try:
            for name in sorted(os.listdir(_BUNDLED_FONT_DIR)):
                if name.lower().endswith(".ttf"):
                    return ImageFont.truetype(os.path.join(_BUNDLED_FONT_DIR, name), size)
        except Exception:
            pass
        try:
            return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def _call_llm_with_fallback(self, context, prompt, fallback_text):
        try:
            return run_llm(context, "You are a witty, creative book publisher. Respond with ONLY the requested text, no explanations or markdown.", prompt)
        except Exception as e:
            print(f"[MiniBookFrontMatter] LLM generation failed: {e}. Using fallback.")
            return fallback_text

    def _wrap_text_centered(self, text, font, max_width, draw):
        """Word-wrap text and return lines for centered rendering."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _compose_title_page(self, title, author_name, page_w, page_h, font_path):
        """Create a elegant title page."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))
        draw = ImageDraw.Draw(page)

        # Title — large and centered at ~35% down the page
        title_size = min(96, max(48, page_w // 12))
        title_font = self._load_font(font_path, title_size)
        text_width = int(page_w * 0.7)

        title_lines = self._wrap_text_centered(title, title_font, text_width, draw)
        line_height = int(title_size * 1.3)
        total_title_height = len(title_lines) * line_height
        title_y = int(page_h * 0.35) - total_title_height // 2

        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            line_w = bbox[2] - bbox[0]
            x = (page_w - line_w) // 2
            draw.text((x, title_y), line, fill=(30, 25, 20), font=title_font)
            title_y += line_height

        # Decorative divider
        div_y = title_y + int(title_size * 0.6)
        div_w = int(page_w * 0.2)
        div_x = (page_w - div_w) // 2
        draw.line([(div_x, div_y), (div_x + div_w, div_y)], fill=(140, 130, 110), width=2)

        # Author name — below the divider
        author_size = int(title_size * 0.45)
        author_font = self._load_font(font_path, author_size)
        author_bbox = draw.textbbox((0, 0), author_name, font=author_font)
        author_w = author_bbox[2] - author_bbox[0]
        author_x = (page_w - author_w) // 2
        author_y = div_y + int(title_size * 0.8)
        draw.text((author_x, author_y), author_name, fill=(80, 70, 60), font=author_font)

        # "A MiniBook Production" at the very bottom
        footer_size = int(title_size * 0.25)
        footer_font = self._load_font(font_path, footer_size)
        footer_text = "A MiniBook Production"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
        footer_w = footer_bbox[2] - footer_bbox[0]
        draw.text(
            ((page_w - footer_w) // 2, page_h - int(page_h * 0.08)),
            footer_text, fill=(160, 150, 140), font=footer_font
        )

        return page

    def _compose_copyright_page(self, title, author_name, page_w, page_h, font_path):
        """Create a simple copyright/colophon page."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))
        draw = ImageDraw.Draw(page)

        font_size = max(20, page_w // 60)
        font = self._load_font(font_path, font_size)
        line_height = int(font_size * 2.0)

        import datetime
        year = datetime.datetime.now().year

        lines = [
            f"{title}",
            "",
            f"Written by {author_name}",
            "",
            f"© {year} {author_name}. All rights reserved.",
            "",
            "This is a work of fiction. Names, characters, places,",
            "and incidents either are the product of the author's",
            "imagination or are used fictitiously.",
            "",
            "",
            "Generated with MiniBook",
            f"Published {year}",
        ]

        margin_left = int(page_w * 0.12)
        y = int(page_h * 0.65)  # Copyright pages are typically pushed down

        for line in lines:
            if line == "":
                y += int(line_height * 0.4)
                continue
            draw.text((margin_left, y), line, fill=(100, 90, 80), font=font)
            y += line_height

        return page

    def _compose_dedication_page(self, dedication_text, page_w, page_h, font_path):
        """Create a dedication page — centered, italic feel, lots of whitespace."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))
        draw = ImageDraw.Draw(page)

        font_size = max(28, page_w // 40)
        font = self._load_font(font_path, font_size)
        text_width = int(page_w * 0.6)

        lines = self._wrap_text_centered(dedication_text, font, text_width, draw)
        line_height = int(font_size * 1.8)
        total_height = len(lines) * line_height

        # Center vertically, slightly above middle
        start_y = int(page_h * 0.40) - total_height // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            x = (page_w - line_w) // 2
            draw.text((x, start_y), line, fill=(60, 50, 45), font=font)
            start_y += line_height

        return page

    def _compose_toc_page(self, editorial_plan, page_w, page_h, font_path):
        """Create a table of contents from chapter openers in the editorial plan."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))
        draw = ImageDraw.Draw(page)

        title_size = max(36, page_w // 25)
        body_size = max(24, page_w // 45)
        title_font = self._load_font(font_path, title_size)
        body_font = self._load_font(font_path, body_size)

        margin_left = int(page_w * 0.15)
        margin_right = int(page_w * 0.15)

        # Title: "Contents"
        toc_title = "Contents"
        title_bbox = draw.textbbox((0, 0), toc_title, font=title_font)
        title_w = title_bbox[2] - title_bbox[0]
        draw.text(((page_w - title_w) // 2, int(page_h * 0.12)), toc_title, fill=(40, 35, 30), font=title_font)

        # Parse editorial plan for chapter openers
        try:
            plan = json.loads(editorial_plan) if isinstance(editorial_plan, str) else editorial_plan
        except json.JSONDecodeError:
            plan = {"pages": []}

        entries = []
        for p in plan.get("pages", []):
            if p.get("type") in ("chapter_opener", "section_break"):
                text = p.get("text", "").split('\n')[0].strip()
                if text:
                    entries.append((text, p.get("page_number", "?")))

        if not entries:
            # Fallback: generate simple numbered entries
            total = plan.get("total_pages", 0)
            for i in range(1, min(total + 1, 20)):
                entries.append((f"Page {i}", i))

        y = int(page_h * 0.22)
        line_height = int(body_size * 2.5)

        for entry_text, page_num in entries:
            # Truncate long entries
            if len(entry_text) > 50:
                entry_text = entry_text[:47] + "..."

            page_str = str(page_num)
            text_bbox = draw.textbbox((0, 0), entry_text, font=body_font)
            num_bbox = draw.textbbox((0, 0), page_str, font=body_font)
            text_w = text_bbox[2] - text_bbox[0]
            num_w = num_bbox[2] - num_bbox[0]

            # Draw entry text on the left
            draw.text((margin_left, y), entry_text, fill=(40, 35, 30), font=body_font)

            # Draw page number on the right
            num_x = page_w - margin_right - num_w
            draw.text((num_x, y), page_str, fill=(40, 35, 30), font=body_font)

            # Draw dotted leader between text and number
            leader_start = margin_left + text_w + 10
            leader_end = num_x - 10
            leader_y = y + body_size // 2
            dot_spacing = body_size // 2
            for dx in range(int(leader_start), int(leader_end), dot_spacing):
                draw.ellipse(
                    [(dx, leader_y - 1), (dx + 2, leader_y + 1)],
                    fill=(160, 150, 140)
                )

            y += line_height

            if y > page_h - int(page_h * 0.15):
                break  # Don't overflow

        return page

    def _compose_author_bio_page(self, bio_text, author_name, page_w, page_h, font_path):
        """Create an 'About the Author' page."""
        page = Image.new('RGB', (page_w, page_h), (252, 250, 245))
        draw = ImageDraw.Draw(page)

        title_size = max(32, page_w // 30)
        body_size = max(22, page_w // 50)
        title_font = self._load_font(font_path, title_size)
        body_font = self._load_font(font_path, body_size)

        margin = int(page_w * 0.15)
        text_width = page_w - margin * 2

        # Title
        about_title = "About the Author"
        title_bbox = draw.textbbox((0, 0), about_title, font=title_font)
        title_w = title_bbox[2] - title_bbox[0]
        title_y = int(page_h * 0.15)
        draw.text(((page_w - title_w) // 2, title_y), about_title, fill=(40, 35, 30), font=title_font)

        # Divider
        div_y = title_y + title_size + int(title_size * 0.5)
        div_w = int(page_w * 0.2)
        div_x = (page_w - div_w) // 2
        draw.line([(div_x, div_y), (div_x + div_w, div_y)], fill=(160, 140, 120), width=2)

        # Bio text
        bio_y = div_y + int(title_size * 1.0)
        line_height = int(body_size * 1.8)

        paragraphs = bio_text.split('\n')
        for para in paragraphs:
            para = para.strip()
            if not para:
                bio_y += int(line_height * 0.5)
                continue

            lines = self._wrap_text_centered(para, body_font, text_width, draw)
            for line in lines:
                if bio_y + line_height > page_h - int(page_h * 0.1):
                    break
                draw.text((margin, bio_y), line, fill=(50, 45, 40), font=body_font)
                bio_y += line_height

        return page

    def _pil_to_tensor(self, pil_img):
        return torch.tensor(np.array(pil_img).astype(np.float32) / 255.0).unsqueeze(0)

    def generate(self, editorial_plan, raw_story, author_name, sheet_size, font, context,
                 include_dedication=True, include_toc=True, include_author_bio=True,
                 include_back_blurb=True):
        """Main execution: generate front and back matter pages."""

        page_w, page_h = self.SHEET_DIMS.get(sheet_size, (1800, 2700))

        # Extract title from editorial plan
        try:
            plan = json.loads(editorial_plan) if isinstance(editorial_plan, str) else editorial_plan
            title = plan.get("title", "Untitled")
        except (json.JSONDecodeError, AttributeError):
            title = "Untitled"
            plan = {}

        # --- FRONT MATTER ---
        front_pages = []

        # 1. Title Page (always included)
        front_pages.append(self._pil_to_tensor(
            self._compose_title_page(title, author_name, page_w, page_h, font)
        ))

        # 2. Copyright Page (always included)
        front_pages.append(self._pil_to_tensor(
            self._compose_copyright_page(title, author_name, page_w, page_h, font)
        ))

        # 3. Dedication Page (optional, LLM-generated)
        if include_dedication:
            dedication_prompt = (
                f"Write a short, evocative book dedication (1-3 sentences) for a book titled "
                f"'{title}'. The story is about: {raw_story[:300]}... "
                f"Make it feel genuine and slightly poetic. Just the dedication text, nothing else."
            )
            dedication_text = self._call_llm_with_fallback(context, dedication_prompt, "Dedicated to the imagination of the reader.")
            front_pages.append(self._pil_to_tensor(
                self._compose_dedication_page(dedication_text, page_w, page_h, font)
            ))

        # 4. Table of Contents (optional)
        if include_toc:
            front_pages.append(self._pil_to_tensor(
                self._compose_toc_page(editorial_plan, page_w, page_h, font)
            ))

        front_tensor = torch.cat(front_pages, dim=0)

        # --- BACK MATTER ---
        back_pages = []

        # 1. Author Bio (optional, LLM-generated)
        if include_author_bio:
            bio_prompt = (
                f"Write a fun, fictional 'About the Author' bio (3-4 sentences) for '{author_name}', "
                f"who just wrote a book titled '{title}'. The story is about: {raw_story[:200]}... "
                f"Make the bio witty and engaging, as if it would appear on the back flap of a real book. "
                f"Just the bio text, nothing else."
            )
            bio_text = self._call_llm_with_fallback(context, bio_prompt, f"About the Author:\n{author_name} is a visionary storyteller exploring new frontiers in AI-assisted literature.")
            back_pages.append(self._pil_to_tensor(
                self._compose_author_bio_page(bio_text, author_name, page_w, page_h, font)
            ))

        # 2. Back Cover Blurb (optional, LLM-generated)
        if include_back_blurb:
            blurb_prompt = (
                f"Write a compelling back-cover blurb (4-6 sentences) for a book titled '{title}'. "
                f"The story is about: {raw_story[:400]}... "
                f"Write it as a real publisher would — hook the reader, create intrigue, "
                f"end with a question or cliff-hanger. Just the blurb text, nothing else."
            )
            blurb_text = self._call_llm_with_fallback(context, blurb_prompt, f"A thrilling journey into the world of '{title}'. Turn the page and discover a story that will challenge everything you thought you knew.")

            # Compose as a simple centered text page
            back_pages.append(self._pil_to_tensor(
                self._compose_dedication_page(blurb_text, page_w, page_h, font)
            ))

        if not back_pages:
            # Ensure we always have at least one back page
            blank = Image.new('RGB', (page_w, page_h), (252, 250, 245))
            back_pages.append(self._pil_to_tensor(blank))

        back_tensor = torch.cat(back_pages, dim=0)

        return (front_tensor, back_tensor)
