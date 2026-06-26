import re

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

class MasterBookControl:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "format": ("STRING", {"default": "children's book"}),
            "theme": ("STRING", {"default": "arguing gets you nowhere", "multiline": True}),
            "constraints": ("STRING", {"default": "Keep it entertaining for adults.", "multiline": True}),
            "art_style": ("STRING", {"default": "Line art illustration with gentle, broad sweeping ink washes"}),
            "character_description": ("STRING", {"default": "Visual description of characters", "multiline": True}),
        }}
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("story_prompt", "art_style", "character_description")
    FUNCTION = "construct"
    CATEGORY = "MiniBook"
    
    def construct(self, format, theme, constraints, art_style, character_description):
        prompt = f"Write a full, continuous {format} with the theme '{theme}'.\nAdditional constraints: {constraints}.\n\nWrite pure story text, do NOT include page numbers, bracketed tags, or scene descriptions. Just write the story from start to finish."
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

from .interleave import InterleaveImageLists
from .dual_llm_nodes import MiniBookFormatter, MiniBookArtDirectorPrompt, MiniBookPromptParser

NODE_CLASS_MAPPINGS = {
    "MiniBookTextParser": MiniBookTextParser,
    "PromptConstructor": PromptConstructor,
    "PromptConstructorV2": PromptConstructorV2,
    "MasterBookControl": MasterBookControl,
    "InterleaveImageLists": InterleaveImageLists,
    "MiniBookFormatter": MiniBookFormatter,
    "MiniBookArtDirectorPrompt": MiniBookArtDirectorPrompt,
    "MiniBookPromptParser": MiniBookPromptParser
}
