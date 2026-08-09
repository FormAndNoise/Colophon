"""
MiniBook Editorial Art Director Node
=====================================
Bridges the Literary Editor's editorial plan to the image generation pipeline.
Extracts illustration notes from the editorial plan and formats them as
proper scene prompts incorporating art style and character descriptions.
"""

import json
import re


class MiniBookEditorialArtDirector:
    """
    Reads the editorial plan JSON and extracts illustration requirements
    only for pages that need them (text_with_illustration, full_illustration).
    Formats each as a complete scene prompt for the image generator.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "editorial_plan": ("STRING", {"multiline": True, "forceInput": True}),
                "art_style": ("STRING", {"forceInput": True}),
                "character_description": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("scene_prompts", "illustration_page_indices")
    OUTPUT_IS_LIST = (True, True)
    FUNCTION = "direct"
    CATEGORY = "MiniBook"

    def direct(self, editorial_plan, art_style, character_description):
        """Extract illustration notes and build scene prompts."""

        try:
            plan = json.loads(editorial_plan) if isinstance(editorial_plan, str) else editorial_plan
        except json.JSONDecodeError:
            raise RuntimeError(
                "[MiniBookEditorialArtDirector] Could not parse editorial plan JSON."
            )

        illustration_types = {"text_with_illustration", "full_illustration"}
        scene_prompts = []
        illustration_indices = []

        for i, page in enumerate(plan.get("pages", [])):
            page_type = page.get("type", "text_only")

            if page_type in illustration_types:
                # Get the illustration note from the editor
                illust_note = page.get("illustration_note", "")
                page_text = page.get("text", "")

                if not illust_note or illust_note.lower() == "null":
                    # Fallback: use first sentence of page text as scene description
                    sentences = re.split(r'[.!?]', page_text)
                    illust_note = sentences[0].strip() if sentences else "A scene from the story"

                # Build a complete scene prompt
                prompt = (
                    f"{art_style}, {illust_note}. "
                    f"Characters: {character_description}. "
                    f"High quality, detailed, consistent style."
                )

                scene_prompts.append(prompt)
                illustration_indices.append(i)

        if not scene_prompts:
            # Fallback: at least one illustration
            scene_prompts.append(
                f"{art_style}. A key scene from the story. "
                f"Characters: {character_description}. High quality, detailed."
            )
            illustration_indices.append(0)

        return (scene_prompts, illustration_indices)


class MiniBookAssembler:
    """
    Concatenates front matter pages + body pages + back matter pages
    into a single ordered batch for PDF export.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "body_pages": ("IMAGE",),
            },
            "optional": {
                "front_pages": ("IMAGE",),
                "back_pages": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("complete_book",)
    FUNCTION = "assemble"
    CATEGORY = "MiniBook"

    @staticmethod
    def _fit_to_body(front_or_back_pages, body_pages):
        """Resize a page batch to the body page's HxW if they differ.

        Batches are NHWC; interpolate needs NCHW, so permute both ways.
        """
        import torch.nn.functional as F

        if front_or_back_pages.shape[1:3] == body_pages.shape[1:3]:
            return front_or_back_pages
        h, w = body_pages.shape[1], body_pages.shape[2]
        pages = front_or_back_pages.permute(0, 3, 1, 2)  # NHWC -> NCHW
        pages = F.interpolate(pages, size=(h, w), mode='bilinear', align_corners=False)
        return pages.permute(0, 2, 3, 1)  # NCHW -> NHWC

    def assemble(self, body_pages, front_pages=None, back_pages=None):
        """Concatenate all page batches in book order."""
        import torch

        parts = []

        if front_pages is not None:
            parts.append(self._fit_to_body(front_pages, body_pages))

        parts.append(body_pages)

        if back_pages is not None:
            parts.append(self._fit_to_body(back_pages, body_pages))

        complete = torch.cat(parts, dim=0)
        return (complete,)
