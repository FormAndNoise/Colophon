"""
Core control and utility nodes recovered from the original monolithic __init__.py.

Contains the MiniBook text/prompt control nodes plus the BookTools suite
(prompt scheduling, loopback, font download, text overlays, etc.).
"""

import os
import re
import random
from PIL import Image, ImageDraw, ImageFont
import torch
import numpy as np

# ComfyUI's top-level module (provides interrupt_processing). Resolved via
# ComfyUI's sys.path at runtime; unrelated to this package's `nodes/` folder.
try:
    from nodes import interrupt_processing
except Exception:
    def interrupt_processing():
        pass


# Bundled fonts ship with the pack; use them as a portable fallback so text
# nodes render with a real TTF when the user-configured font path is missing.
_BUNDLED_FONT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts"
)


def _bundled_font_fallback():
    """Return the path of the first bundled .ttf, or None if unavailable."""
    try:
        for name in sorted(os.listdir(_BUNDLED_FONT_DIR)):
            if name.lower().endswith(".ttf"):
                return os.path.join(_BUNDLED_FONT_DIR, name)
    except OSError:
        pass
    return None


def _safe_truetype(font_path, size):
    """Load a TTF with fallbacks: requested path -> bundled font -> Windows
    arial -> Pillow's embedded default. Never raises for a missing font."""
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    bundled = _bundled_font_fallback()
    if bundled:
        try:
            return ImageFont.truetype(bundled, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


class MiniBookTextParser:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"text": ("STRING", {"forceInput": True})}}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("page_texts", "scene_prompts")
    OUTPUT_IS_LIST = (True, True)
    FUNCTION = "parse"
    CATEGORY = "MiniBook"

    def parse(self, text):
        import os
        try:
            import folder_paths
            output_dir = folder_paths.get_output_directory()
        except Exception:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output")
        os.makedirs(output_dir, exist_ok=True)
        raw_output_path = os.path.join(output_dir, 'raw_llm_output.txt')
        with open(raw_output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        pages = [p.strip() for p in re.findall(r'\[PAGE[_\s]*\d+\]:?(.*?)(?=\[|$)', text, re.DOTALL|re.IGNORECASE)]
        scenes = [s.strip() for s in re.findall(r'\[SCENE[_\s]*\d+\]:?(.*?)(?=\[|$)', text, re.DOTALL|re.IGNORECASE)]
        min_len = min(len(pages), len(scenes))
        if min_len == 0:
             return (["Error parsing text"], ["Error parsing scenes"])
        return (pages[:min_len], scenes[:min_len])


class PromptConstructor:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "theme": ("STRING", {"forceInput": True}),
            "format": ("STRING", {"forceInput": True})
        }}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "construct"
    CATEGORY = "MiniBook"

    def construct(self, theme, format):
        return (f"Write a {format} with the theme '{theme}'. Include 8 pages, each with text and an illustration.\nUse this format:\n[TITLE]: Title of the book\n[CHARACTER]: Visual description of characters\n[PAGE_N]: Text content for the page\n[SCENE_N]: Scene prompt for the page illustration",)


class TextInput:
    """Simple multiline text input node (restored from the original MiniBook pack;
    registered as MiniBookTextInput, which existing workflows depend on)."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "get_text"
    CATEGORY = "MiniBook"

    def get_text(self, text):
        return (text,)


class MasterBookControl:
    """Connection-based book control (matches the interface existing workflows
    were built against: all inputs are wired from TextInput nodes)."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "format": ("STRING", {"multiline": False, "forceInput": True}),
                "theme": ("STRING", {"multiline": True, "forceInput": True}),
                "constraints": ("STRING", {"multiline": True, "forceInput": True}),
                "art_style": ("STRING", {"multiline": True, "forceInput": True}),
                "character_description": ("STRING", {"multiline": True, "forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompt", "art_style", "character_description")
    FUNCTION = "build_prompt"
    CATEGORY = "MiniBook"

    def build_prompt(self, format, theme, constraints, art_style, character_description):
        prompt = (f"Write a {format} about {theme}.\n"
                  f"Constraints: {constraints}\n"
                  f"Art Style: {art_style}\n"
                  f"Key Characters: {character_description}")
        return (prompt, art_style, character_description)


class PromptConstructorV2:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "theme": ("STRING", {"forceInput": True}),
            "format": ("STRING", {"forceInput": True}),
            "art_style": ("STRING", {"forceInput": True}),
            "constraints": ("STRING", {"forceInput": True})
        }}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "construct"
    CATEGORY = "MiniBook"

    def construct(self, theme, format, art_style, constraints):
        prompt = f"Write a {format} with the theme '{theme}'. Include 8 pages, each with text and an illustration.\nThe art style for the illustrations is: {art_style}.\nAdditional constraints: {constraints}.\n\nUse this exact format for your response:\n[TITLE]: Title of the book\n[CHARACTER]: Visual description of characters\n[PAGE_N]: Text content for the page\n[SCENE_N]: Scene prompt for the page illustration (make sure the scene prompt includes the art style: {art_style})"
        return (prompt,)


class AnyType(str):
    """A special class that is always equal in not equal comparisons. Credit to pythongosssss"""

    def __ne__(self, __value: object) -> bool:
        return False


any = AnyType("*")
loop_interation = 0
reset_global = False


class BookToolsPromptSelector:
    """
    Selects and concatenates values from a dictionary based on input indices and ranges.
    The input string contains 1-based indices which are converted to dictionary keys.
    Accepts comma-separated indices and inclusive ranges, e.g. "1,2,3" or "1-3,5".
    Assumes the dictionary values are strings which will be concatenated and returned as a single string.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "dictionary": ("DICTIONARY", ),
                "selected_indexes": ("STRING", {
                    "multiline": False,
                    "default": "1,2,3"
                }),
            }
        }

    RETURN_TYPES = ("STRING", )
    FUNCTION = "main"
    CATEGORY = "selector"
    OUTPUT_NODE = False

    @staticmethod
    def _parse_indexes(selected_indexes):
        """Parse "1,2,3" / "1-3,5" style index specs into a list of 1-based ints."""
        indexes = []
        for token in str(selected_indexes).split(','):
            token = token.strip()
            if not token:
                continue
            if '-' in token:
                start_s, _, end_s = token.partition('-')
                try:
                    start, end = int(start_s.strip()), int(end_s.strip())
                except ValueError:
                    raise ValueError(f"Invalid index range in selected_indexes: {token!r}")
                indexes.extend(range(start, end + 1))
            else:
                try:
                    indexes.append(int(token))
                except ValueError:
                    raise ValueError(f"Invalid index in selected_indexes: {token!r}")
        return indexes

    def main(self, dictionary: dict, selected_indexes):
        if not isinstance(dictionary, dict):
            raise ValueError("dictionary input must be a dictionary.")

        # Legacy graphs may still deliver a plain INT widget value.
        if isinstance(selected_indexes, int):
            return (str(dictionary.get(str(selected_indexes), '')),)

        if not isinstance(selected_indexes, str):
            raise ValueError(
                "selected_indexes must be a string of 1-based indices, "
                "e.g. '1,2,3' or '1-3'."
            )

        parts = [str(dictionary.get(str(i), '')) for i in self._parse_indexes(selected_indexes)]
        return ('\n'.join(parts),)


class BookToolsPromptSchedule:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"text": ("STRING", {"multiline": True, "default":"\"first page description\",\n\"second page description\""}),
            "before_text": ("STRING", {"multiline": True,}),
            "after_text": ("STRING", {"multiline": True,}),
            }}

    RETURN_TYPES = ("DICTIONARY",)
    FUNCTION = "main"
    CATEGORY = "prompt"
    OUTPUT_NODE = False

    def main(self, text, before_text, after_text):
        segments = text.split('",')
        formatted_texts = {}

        for index, segment in enumerate(segments, start=1):
            cleaned_segment = segment.replace('"', '').strip()
            parts = [part for part in [before_text.strip(), cleaned_segment, after_text.strip()] if part]
            formatted_text = ', '.join(parts)
            formatted_texts[str(index)] = formatted_text
        return (formatted_texts,)


class BookToolsLoop:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"reset": ("BOOLEAN", {"default": False}),}}

    RETURN_TYPES = ("LOOP", "INT",)
    FUNCTION = "run"
    CATEGORY = "loopback"
    RETURN_NAMES = ("LOOP", "Iteration",)

    def run(self, reset):
        global loop_interation, reset_global
        if (reset == True):
            loop_interation = 1
            reset_global = True
        else:
            reset_global = False
        return (self, loop_interation)

    @classmethod
    def IS_CHANGED(self, reset):
        global loop_interation, reset_global
        loop_interation +=1
        if (reset == True):
            loop_interation = 1
            reset_global = True
        else:
            reset_global = False
        return loop_interation


class BookToolsLoopStart:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "first_loop": (any,),
            "loop": ("LOOP",)
            }
        }

    FUNCTION = "run"
    CATEGORY = "loopback"
    RETURN_TYPES = (any,)
    RETURN_NAMES = ("*",)

    def run(self, first_loop, loop):
        # reset_global is read-only here (assigned by BookToolsLoop); no
        # `global` declaration needed for reads.
        if reset_global == True:
            return (first_loop,)
        if hasattr(loop, 'next'):
            return (loop.next,)
        return (first_loop,)

    @classmethod
    def IS_CHANGED(self, first_loop, loop):
        if reset_global == True:
            return (first_loop,)
        if hasattr(loop, 'next'):
            return id(loop.next)
        return float("NaN")


class BookToolsLoopEnd:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "send_to_next_loop": (any, ), "loop": ("LOOP",) }}
    FUNCTION = "run"
    CATEGORY = "loopback"
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    def run(self, send_to_next_loop, loop):
        loop.next = send_to_next_loop
        return ()


class BookToolsEndQueue:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "boolean": ("BOOLEAN", {"default": False}), }}
    FUNCTION = "main"
    CATEGORY = "logic"
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    def main(self, boolean):
        if (boolean==True):
            interrupt_processing()
        return ()


class BookToolsDownloadFont:

    SUPPORTED_FONTS = {
        "Delius": "Delius:wght@400",
        "DejaVuSans-Bold": "DejaVuSans-Bold",
        "FreeMono": "FreeMono:wght@400",
        "Roboto": "RobotoMono-VariableFont_wght",
        "Baloo 2": "Baloo2-VariableFont_wght",
        "LuckiestGuy": "LuckiestGuy",
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Default must be a member of the option list; ComfyUI combo
                # widgets reject (or silently mis-send) out-of-list defaults.
                "font_name": (list(cls.SUPPORTED_FONTS.keys()), {"default": "Delius"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "download_font"
    CATEGORY = "image/text"

    def download_font(self, font_name):
        import requests
        import os
        from urllib.parse import urlparse

        fallback_font = "C:/Windows/Fonts/arial.ttf"

        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
        os.makedirs(fonts_dir, exist_ok=True)

        if font_name not in self.SUPPORTED_FONTS:
            raise ValueError(f"Unsupported font: {font_name!r}")

        font_filename = self.SUPPORTED_FONTS[font_name] + ".ttf"
        font_path = os.path.join(fonts_dir, font_filename)

        if os.path.exists(font_path):
            try:
                ImageFont.truetype(font_path, 12)
                return (font_path,)
            except Exception:
                print(f"Cached font {font_name} is corrupt, attempting redownload...")
                os.remove(font_path)

        api_url = f"https://fonts.googleapis.com/css2?family={self.SUPPORTED_FONTS[font_name]}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:

            response = requests.get(api_url, headers=headers, timeout=(10, 30))
            response.raise_for_status()
            css = response.text

            for line in css.split('\n'):
                if 'src:' in line and 'url(' in line:
                    start = line.find('url(') + 4
                    end = line.find(')', start)
                    font_url = line[start:end].strip()
                    break
            else:
                raise ValueError("Could not find font URL in CSS")

            parsed_url = urlparse(font_url)
            if parsed_url.scheme != "https" or parsed_url.hostname != "fonts.gstatic.com":
                raise ValueError("Invalid font URL")

            font_response = requests.get(font_url, headers=headers, timeout=(10, 60))
            font_response.raise_for_status()
            if len(font_response.content) > 20 * 1024 * 1024:
                raise ValueError("Downloaded font exceeds the 20 MiB safety limit")

            with open(font_path, 'wb') as f:
                f.write(font_response.content)

            try:
                ImageFont.truetype(font_path, 12)
                return (font_path,)
            except Exception as e:
                print(f"Downloaded font {font_name} is invalid: {str(e)}")
                if os.path.exists(font_path):
                    os.remove(font_path)
                raise

        except Exception as e:
            print(f"Error downloading font {font_name}: {str(e)}")
            print(f"Falling back to default font: {fallback_font}")
            return (fallback_font,)


class BookToolsImageTextOverlay:
    def __init__(self, device="cpu"):
        self.device = device
    _alignments = ["left", "right", "center"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"multiline": True, "default": "Hello"}),
                "textbox_width": ("INT", {"default": 200, "min": 1}),
                "textbox_height": ("INT", {"default": 200, "min": 1}),
                "max_font_size": ("INT", {"default": 80, "min": 1, "max": 256, "step": 1}),
                "min_font_size": ("INT", {"default": 12, "min": 1, "max": 256, "step": 1}),
                "font": ("STRING", {"default": "C:/Windows/Fonts/arial.ttf"}),
                "alignment": (cls._alignments, {"default": "center"}),
                "color": ("STRING", {"default": "#000000"}),
                "start_x": ("INT", {"default": 0}),
                "start_y": ("INT", {"default": 0}),
                "padding": ("INT", {"default": 50}),
                "line_height_factor": ("FLOAT", {"default": 1.2, "min": 0.5, "max": 3.0, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "add_text_overlay"
    CATEGORY = "image/text"

    def calculate_text_width(self, text, font):
        """Calculate exact text width including kerning if available"""
        try:

            from PIL import ImageDraw
            dummy_image = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(dummy_image)
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]
        except Exception:
            # Fall back to per-character widths; keep this narrow so a real
            # interrupt (KeyboardInterrupt/SystemExit) still propagates.
            return sum(font.getbbox(char)[2] - font.getbbox(char)[0] for char in text)

    def calculate_text_size(self, text, font_size, font_path, max_width, max_height, line_height_factor):
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"Font error: {str(e)}, using default")
            font = ImageFont.load_default()

        paragraphs = text.split('\n')
        lines = []
        max_line_width = 0

        for paragraph in paragraphs:

            words = paragraph.split()
            if not words:
                lines.append("")
                continue

            current_line = []
            current_width = 0

            for word in words:
                word_bbox = font.getbbox(word)
                word_width = word_bbox[2] - word_bbox[0]

                space_width = font.getbbox(' ')[2] if current_line else 0

                if current_width + word_width + space_width <= max_width:
                    if current_line:
                        current_width += space_width
                    current_line.append(word)
                    current_width += word_width
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        max_line_width = max(max_line_width, current_width)
                    current_line = [word]
                    current_width = word_width

            if current_line:
                lines.append(' '.join(current_line))
                max_line_width = max(max_line_width, current_width)

        line_height = int(font_size * line_height_factor)
        total_height = len(lines) * line_height

        fits = (max_line_width <= max_width) and (total_height <= max_height)

        return lines, fits, max_line_width, total_height

    def add_text_overlay(self, image, text, textbox_width, textbox_height, max_font_size, min_font_size,
                        font, alignment, color, start_x, start_y, padding, line_height_factor):
        image_tensor = image
        image_np = image_tensor.cpu().numpy()
        image_pil = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))
        color_rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

        effective_width = textbox_width - 2 * padding
        effective_height = textbox_height - 2 * padding

        low, high = min_font_size, max_font_size
        optimal_font_size = min_font_size
        optimal_lines = []

        while low <= high:
            mid = (low + high) // 2
            lines, fits, _, _ = self.calculate_text_size(text, mid, font, effective_width, effective_height, line_height_factor)

            if fits:
                optimal_font_size = mid
                optimal_lines = lines
                low = mid + 1
            else:
                high = mid - 1

        if not optimal_lines:
            optimal_font_size = min_font_size
            optimal_lines, _, _, _ = self.calculate_text_size(text, min_font_size, font, effective_width, effective_height, line_height_factor)

        loaded_font = _safe_truetype(font, optimal_font_size)
        draw = ImageDraw.Draw(image_pil)

        line_height = int(optimal_font_size * line_height_factor)
        total_text_height = len(optimal_lines) * line_height
        y = start_y + padding

        if total_text_height <= effective_height:
            y += (effective_height - total_text_height) // 2

        for line in optimal_lines:
            if y + line_height > start_y + textbox_height:
                break

            line_width = self.calculate_text_width(line, loaded_font)

            if alignment == "left":
                x = start_x + padding
            elif alignment == "right":
                x = start_x + effective_width - line_width + padding
            else:

                x = start_x + (effective_width - line_width) // 2 + padding

            draw.text((x, y), line, fill=color_rgb, font=loaded_font)
            y += line_height

        image_tensor_out = torch.tensor(np.array(image_pil).astype(np.float32) / 255.0)
        image_tensor_out = torch.unsqueeze(image_tensor_out, 0)
        return (image_tensor_out,)


class BookToolsCalculateTextGrowth:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "Hello"}),
                "mask_width": ("INT", {"default": 200, "min": 1}),
                "mask_height": ("INT", {"default": 200, "min": 1}),
                "min_font_size": ("INT", {"default": 12, "min": 1, "max": 256, "step": 1}),
                "font": ("STRING", {"default": "C:/Windows/Fonts/arial.ttf"}),
                "padding": ("INT", {"default": 50}),
                "line_height_factor": ("FLOAT", {"default": 1.2, "min": 0.5, "max": 3.0, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("growth_percentage",)
    FUNCTION = "calculate"
    CATEGORY = "image/text"

    def calculate_text_bounds(self, text, font_size, font_path, max_width, line_height_factor):
        font = _safe_truetype(font_path, font_size)
        paragraphs = text.split('\n')
        max_line_width = 0
        total_lines = 0

        for paragraph in paragraphs:
            words = paragraph.split()
            current_line = []
            current_width = 0

            for word in words:
                word_bbox = font.getbbox(word)
                word_width = word_bbox[2] - word_bbox[0]
                space_width = font.getbbox(' ')[2] if current_line else 0

                if current_width + word_width + space_width <= max_width:
                    current_line.append(word)
                    current_width += word_width + space_width
                else:
                    max_line_width = max(max_line_width, current_width)
                    current_line = [word]
                    current_width = word_width
                    total_lines += 1

            if current_line:
                max_line_width = max(max_line_width, current_width)
                total_lines += 1

        line_height = int(font_size * line_height_factor)
        total_height = total_lines * line_height

        return max_line_width, total_height

    def calculate(self, text, mask_width, mask_height, min_font_size, font, padding, line_height_factor):
        # The text box is the mask plus padding on each side, and the layout
        # wraps against the box interior — which is exactly the mask width.
        text_width, text_height = self.calculate_text_bounds(
            text, min_font_size, font, mask_width, line_height_factor
        )

        width_ratio = (text_width / mask_width) / 2
        height_ratio = (text_height / mask_height) / 2

        growth_ratio = max(width_ratio, height_ratio)

        if growth_ratio <= 0.5:
            return (0,)

        growth_percentage = min(100, int((growth_ratio - 0.5) * 200))

        return (growth_percentage,)


class BookToolsRandomTextOverlay:
    def __init__(self, device="cpu"):
        self.device = device
    _alignments = ["left", "center"]
    _positions = ["top", "bottom"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"multiline": True, "default": "Hello"}),
                "font_size": ("INT", {"default": 30, "min": 8, "max": 100, "step": 1}),
                "font": ("STRING", {"default": "C:/Windows/Fonts/arial.ttf"}),
                "color": ("STRING", {"default": "#000000"}),
                "padding": ("INT", {"default": 20, "min": 0}),
                "margin": ("INT", {"default": 20, "min": 0}),
                "corner_radius": ("INT", {"default": 15, "min": 0}),
                "line_height_factor": ("FLOAT", {"default": 1.2, "min": 0.5, "max": 3.0, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "add_random_text_overlay"
    CATEGORY = "image/text"

    def add_random_text_overlay(self, image, text, font_size, font, color, padding, margin, corner_radius, line_height_factor):
        image_tensor = image
        image_np = image_tensor.cpu().numpy()
        image_pil = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))

        # Nothing to overlay: return the image unchanged instead of crashing
        # with max() over an empty sequence.
        if not text or not text.strip():
            image_tensor_out = torch.tensor(np.array(image_pil).astype(np.float32) / 255.0)
            return (torch.unsqueeze(image_tensor_out, 0),)

        image_pil = image_pil.convert('RGBA')
        color_rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

        bg_overlay = Image.new('RGBA', image_pil.size, (0, 0, 0, 0))
        bg_draw = ImageDraw.Draw(bg_overlay)

        text_overlay = Image.new('RGBA', image_pil.size, (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_overlay)

        loaded_font = _safe_truetype(font, font_size)

        max_width = image_pil.width - (margin * 2) - (padding * 2)
        line_height = int(font_size * line_height_factor)
        space_width = text_draw.textlength(" ", font=loaded_font)

        lines = []
        current_line = []
        current_width = 0

        for word in text.split():
            word_width = text_draw.textlength(word, font=loaded_font)

            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width + space_width
            else:
                if current_line:
                    lines.append(" ".join(current_line))

                if word_width > max_width:
                    chars = []
                    char_width = 0
                    for c in word:
                        cw = text_draw.textlength(c, font=loaded_font)
                        if char_width + cw > max_width:
                            lines.append("".join(chars))
                            chars = []
                            char_width = 0
                        chars.append(c)
                        char_width += cw
                    if chars:
                        lines.append("".join(chars))
                else:
                    current_line = [word]
                    current_width = word_width + space_width

        if current_line:
            lines.append(" ".join(current_line))

        max_line_width = max(text_draw.textlength(line, font=loaded_font) for line in lines)
        total_height = len(lines) * line_height

        bg_width = int(max_line_width + padding * 2)
        bg_height = int(total_height + padding * 2)

        position = random.choice(self._positions)
        alignment = random.choice(self._alignments)

        if position == "top":
            bg_y = margin
            opacity = 0.9
        else:
            bg_y = image_pil.height - bg_height - margin
            opacity = 0.8

        if alignment == "left":
            bg_x = margin
        else:
            bg_x = (image_pil.width - bg_width) // 2

        alpha = int(255 * opacity)
        bg_color = (255, 255, 255, alpha)
        bg_draw.rounded_rectangle(
            [bg_x, bg_y, bg_x + bg_width, bg_y + bg_height],
            radius=corner_radius,
            fill=bg_color
        )

        y = bg_y + padding
        for line in lines:
            if y + line_height > bg_y + bg_height:
                break

            line_width = text_draw.textlength(line, font=loaded_font)

            if alignment == "left":
                x = bg_x + padding
            else:
                x = bg_x + (bg_width - line_width) // 2

            text_draw.text((x+1, y+1), line, fill=(255,255,255,150), font=loaded_font)

            text_draw.text((x, y), line, fill=(*color_rgb, 255), font=loaded_font)
            y += line_height

        result = Image.alpha_composite(image_pil, bg_overlay)
        result = Image.alpha_composite(result, text_overlay)

        result = result.convert('RGB')

        image_tensor_out = torch.tensor(np.array(result).astype(np.float32) / 255.0)
        image_tensor_out = torch.unsqueeze(image_tensor_out, 0)
        return (image_tensor_out,)
