import re

class MiniBookFormatter:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "raw_story": ("STRING", {"multiline": True, "forceInput": True}),
            "words_per_page": ("INT", {"default": 30, "min": 5, "max": 500, "step": 1}),
        }}
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("pages_list", "numbered_pages_string")
    OUTPUT_IS_LIST = (True, False)
    FUNCTION = "format_story"
    CATEGORY = "MiniBook"
    
    def format_story(self, raw_story, words_per_page):
        # Split into paragraphs first to respect natural story breaks
        paragraphs = re.split(r'\n\n+', raw_story.strip())
        pages = []
        current_page = ""
        word_count = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            paragraph_words = paragraph.split()
            if word_count + len(paragraph_words) <= words_per_page:
                # Paragraph fits on the current page
                current_page += paragraph + "\n\n"
                word_count += len(paragraph_words)
            else:
                # Flush existing page (if any) before starting a new one
                if current_page.strip():
                    pages.append(current_page.strip())
                # If the paragraph itself exceeds words_per_page, split it at sentence boundaries
                if len(paragraph_words) > words_per_page:
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    current_page = ""
                    word_count = 0
                    for sentence in sentences:
                        sentence_words = sentence.split()
                        if word_count + len(sentence_words) <= words_per_page:
                            current_page += sentence + " "
                            word_count += len(sentence_words)
                        else:
                            if current_page.strip():
                                pages.append(current_page.strip())
                            current_page = sentence + " "
                            word_count = len(sentence_words)
                else:
                    current_page = paragraph + "\n\n"
                    word_count = len(paragraph_words)

        if current_page.strip():
            pages.append(current_page.strip())

        # Ensure we always have at least one page
        if not pages:
            pages = [raw_story.strip()]

        # Add page numbering to the combined string output
        numbered_pages_string = "\n\n".join([f"Page {i+1}:\n{page}" for i, page in enumerate(pages)])

        return (pages, numbered_pages_string)

class MiniBookArtDirectorPrompt:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "numbered_pages_string": ("STRING", {"multiline": True, "forceInput": True}),
            "art_style": ("STRING", {"forceInput": True}),
            "character_description": ("STRING", {"forceInput": True}),
        }}
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("art_director_prompt",)
    FUNCTION = "build_prompt"
    CATEGORY = "MiniBook"
    
    def build_prompt(self, numbered_pages_string, art_style, character_description):
        prompt = f"""You are the Art Director for a book. 
The main character(s) look like this: {character_description}
The global art style is: {art_style}

Here is the story, broken down into pages:
{numbered_pages_string}

For EACH page, write a highly descriptive visual prompt for an AI image generator. 
The prompt MUST include the character description and the art style to maintain consistency.
Output your response EXACTLY in this format:
1. [Prompt for page 1]
2. [Prompt for page 2]
...
(Do not include any other text, just the numbered list).
"""
        return (prompt,)

class MiniBookPromptParser:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "art_director_response": ("STRING", {"multiline": True, "forceInput": True}),
        }}
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("scene_prompts_list",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "parse_prompts"
    CATEGORY = "MiniBook"
    
    def parse_prompts(self, art_director_response):
        # Extract lines starting with digits and a period
        prompts = []
        for line in art_director_response.split('\n'):
            match = re.match(r'^\d+\.\s*(.*)', line.strip())
            if match:
                prompts.append(match.group(1))
                
        if not prompts:
            return (["Error parsing scene prompts. Output was: " + art_director_response],)
            
        return (prompts,)
