from .llm_bridge import run_llm
import re

class MiniBookEarlyReaderGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "theme": ("STRING", {"multiline": True, "default": "A dog finding a bone"}),
                "reading_level": (["Pre-K (Sight Words)", "Kindergarten (CVC)", "1st Grade", "2nd Grade"],),
                "target_vocabulary": ("STRING", {"multiline": True, "default": "cat, sat, mat, hat"}),
                "context": ("LLM_CONTEXT",),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("raw_story",)
    FUNCTION = "generate"
    CATEGORY = "MiniBook"
    
    def generate(self, theme, reading_level, target_vocabulary, context):
        prompt = f"Write a children's book story about: {theme}. The reading level must be exactly: {reading_level}. Emphasize the following target vocabulary words: {target_vocabulary}. Keep sentences short and simple. Output ONLY the story text."
        story = run_llm(context, "You are a children's book author.", prompt, max_tokens=1024)
        return (story,)

class MiniBookBilingualGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "theme": ("STRING", {"multiline": True, "default": "A friendship between a bird and a turtle"}),
                "primary_language": ("STRING", {"default": "English"}),
                "secondary_language": ("STRING", {"default": "Spanish"}),
                "context": ("LLM_CONTEXT",),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("raw_story",)
    FUNCTION = "generate"
    CATEGORY = "MiniBook"
    
    def generate(self, theme, primary_language, secondary_language, context):
        prompt = f"Write a story about: {theme}. For every paragraph, write it first in {primary_language}, followed immediately by the exact translation in {secondary_language} on the next line. Do not use labels like 'English:' or 'Spanish:'. Output ONLY the story text."
        story = run_llm(context, "You are a bilingual author.", prompt, max_tokens=2048)
        return (story,)

class MiniBookWorkbookGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "topic": ("STRING", {"multiline": True, "default": "Mindfulness and Anxiety Relief"}),
                "num_exercises": ("INT", {"default": 10, "min": 3, "max": 50}),
                "context": ("LLM_CONTEXT",),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("raw_story",)
    FUNCTION = "generate"
    CATEGORY = "MiniBook"
    
    def generate(self, topic, num_exercises, context):
        prompt = f"Create a workbook about {topic} with {num_exercises} exercises. For each exercise, write a brief intro/reflection, followed by a writing prompt. After the prompt, add 10-12 lines of underscores (_____________________________) to represent blank lines for the user to write on. Each exercise should feel like a distinct chapter. Output ONLY the workbook text."
        story = run_llm(context, "You are a workbook creator and therapist.", prompt, max_tokens=3000)
        return (story,)

class MiniBookCYOAGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "theme": ("STRING", {"multiline": True, "default": "A space exploration mission gone wrong"}),
                "num_pages": ("INT", {"default": 12, "min": 4, "max": 30}),
                "context": ("LLM_CONTEXT",),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("page_texts", "scene_prompts")
    OUTPUT_IS_LIST = (True, True)
    FUNCTION = "generate"
    CATEGORY = "MiniBook"
    
    def generate(self, theme, num_pages, context):
        prompt = f"Write a Choose Your Own Adventure story about {theme}. It must have exactly {num_pages} pages. \nFormat MUST BE:\n[PAGE 1]\nText for page 1 here, ending with a choice. (e.g. Turn to page 3 to run, Turn to page 4 to hide)\n[SCENE 1]\nPrompt for the illustration of page 1.\n\nContinue this for all {num_pages} pages. Make sure the page turn references are logically consistent within the {num_pages} pages. Some pages should be endings. Output ONLY the formatted text."
        raw = run_llm(context, "You are an interactive fiction author.", prompt, max_tokens=4000)
        
        pages = [p.strip() for p in re.findall(r'\[PAGE[_\s]*\d+\]:?(.*?)(?=\[|$)', raw, re.DOTALL|re.IGNORECASE)]
        scenes = [s.strip() for s in re.findall(r'\[SCENE[_\s]*\d+\]:?(.*?)(?=\[|$)', raw, re.DOTALL|re.IGNORECASE)]
        min_len = min(len(pages), len(scenes))
        if min_len == 0:
             return (["Error parsing text. Raw output: " + raw], ["Error parsing scenes"])
        return (pages[:min_len], scenes[:min_len])
