import re

class MiniBookFormatter:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "raw_story": ("STRING", {"multiline": True, "forceInput": True}),
            "words_per_page": ("INT", {"default": 80, "min": 5, "max": 500, "step": 1}),
            "min_words_per_page": ("INT", {"default": 30, "min": 0, "max": 300, "step": 1}),
        }}
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("pages_list", "numbered_pages_string")
    OUTPUT_IS_LIST = (True, False)
    FUNCTION = "format_story"
    CATEGORY = "MiniBook"
    
    def format_story(self, raw_story, words_per_page, min_words_per_page=30):
        # Guard: detect LLM error responses before they create bad "pages"
        stripped = raw_story.strip()
        error_indicators = ["'error':", '"error":', "Connection closed", "Unexpected format"]
        for indicator in error_indicators:
            if indicator in stripped:
                raise RuntimeError(
                    f"[MiniBookFormatter] Story LLM returned an error instead of story text. "
                    f"Check your API key, model name, and OpenRouter account credits.\n"
                    f"Raw response: {stripped[:300]}"
                )
        if len(stripped) < 50:
            raise RuntimeError(
                f"[MiniBookFormatter] Story LLM response is too short to be a valid story ({len(stripped)} chars). "
                f"Response: {stripped}"
            )

        # Split into paragraphs first to respect natural story breaks
        paragraphs = re.split(r'\n\n+', stripped)
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
            pages = [stripped]

        # --- Minimum words merge pass ---
        # Merge any page below min_words_per_page into the next page.
        # Walk forward; if a page is too short, append it to the next and
        # remove it. Repeat until stable (handles runs of short pages).
        if min_words_per_page > 0:
            changed = True
            while changed:
                changed = False
                merged = []
                i = 0
                while i < len(pages):
                    page = pages[i]
                    wc = len(page.split())
                    # If this page is too short AND there's a next page, merge forward
                    if wc < min_words_per_page and i + 1 < len(pages):
                        pages[i + 1] = page + "\n\n" + pages[i + 1]
                        changed = True
                        i += 1  # skip this page, the next absorbs it
                    else:
                        merged.append(page)
                        i += 1
                pages = merged

        # Add page numbering to the combined string output
        numbered_pages_string = "\n\n".join([f"Page {i+1}:\n{page}" for i, page in enumerate(pages)])

        return (pages, numbered_pages_string)

class MiniBookFormatterV2:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "raw_story": ("STRING", {"multiline": True, "forceInput": True}),
            "words_per_page": ("INT", {"default": 40, "min": 10, "max": 500, "step": 5}),
            "format_type": (["storybook", "poetry", "chaptered_story"],),
            "illustration_frequency": ("INT", {"default": 5, "min": 1, "step": 1}),  # 1 illustration per N pages
        }}
    
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("pages_list", "numbered_pages_string", "illustration_positions")
    OUTPUT_IS_LIST = (True, False, True)
    FUNCTION = "format_story"
    CATEGORY = "MiniBook"
    
    def format_story(self, raw_story, words_per_page, format_type, illustration_frequency):
        # Guard: detect LLM error responses
        stripped = raw_story.strip()
        error_indicators = ["'error':", '"error":', "Connection closed", "Unexpected format"]
        for indicator in error_indicators:
            if indicator in stripped:
                raise RuntimeError(
                    f"[MiniBookFormatterV2] Story LLM returned an error instead of story text. "
                    f"Check your API key, model name, and OpenRouter account credits.\n"
                    f"Raw response: {stripped[:300]}"
                )
        if len(stripped) < 50:
            raise RuntimeError(
                f"[MiniBookFormatterV2] Story LLM response is too short to be a valid story ({len(stripped)} chars). "
                f"Response: {stripped}"
            )

        pages = []
        illustration_positions = []
        numbered_pages_string = ""
        current_page = ""
        word_count = 0
        
        if format_type == "chaptered_story":
            # Split text into chapters (detect "Chapter X" or user prompt-based clues)
            chapters = re.split(r"(?=Chapter\s+\d+\:?)", raw_story, flags=re.IGNORECASE)
            chapter_count = 0
            for chapter in chapters:
                chapter_text = chapter.strip()
                
                # If chapter starts with 'Chapter X:', remove it from chapter_text so we don't double it
                chapter_text = re.sub(r"^Chapter\s+\d+\:?\s*", "", chapter_text, flags=re.IGNORECASE)
                if not chapter_text:
                    continue
                
                chapter_count += 1
                chapter_title = f"Chapter {chapter_count}"

                current_page += f"{chapter_title}\n\n"
                for word in chapter_text.split():
                    current_page += word + " "
                    word_count += 1
                    if word_count >= words_per_page:
                        pages.append(current_page.strip())
                        numbered_pages_string += f"Page {len(pages)}:\n{current_page.strip()}\n\n"
                        current_page = ""
                        word_count = 0
                
                # Include illustration position only at the end of each chapter
                # (which is the last page that was created for this chapter, or current_page if it flushed later)
                # Wait, if current_page has leftovers, we should flush it at the end of the chapter.
                if current_page.strip():
                    pages.append(current_page.strip())
                    numbered_pages_string += f"Page {len(pages)}:\n{current_page.strip()}\n\n"
                    current_page = ""
                    word_count = 0

                # Mark the last page of this chapter as the one with an illustration
                if pages:
                    illustration_positions.append(len(pages) - 1)
        elif format_type == "poetry":
            # Split by stanzas (detect line breaks)
            stanzas = raw_story.split("\n\n")
            for stanza in stanzas:
                current_page += stanza.strip() + "\n\n"
                word_count += len(stanza.split())
                if word_count >= words_per_page:
                    pages.append(current_page.strip())
                    numbered_pages_string += f"Page {len(pages)}:\n{current_page.strip()}\n\n"
                    current_page = ""
                    word_count = 0
            if current_page.strip():
                pages.append(current_page.strip())
                numbered_pages_string += f"Page {len(pages)}:\n{current_page.strip()}\n\n"
        else:  # Default: storybook or prose
            paragraphs = re.split(r'\n\n+', raw_story.strip())
            for paragraph in paragraphs:
                paragraph_words = paragraph.split()
                for word in paragraph_words:
                    current_page += word + " "
                    word_count += 1
                    if word_count >= words_per_page:
                        pages.append(current_page.strip())
                        numbered_pages_string += f"Page {len(pages)}:\n{current_page.strip()}\n\n"
                        current_page = ""
                        word_count = 0
            if current_page.strip():
                pages.append(current_page.strip())
                numbered_pages_string += f"Page {len(pages)}:\n{current_page.strip()}\n\n"
        
        # Add illustration positions by interval
        if illustration_frequency > 0 and format_type != "chaptered_story":
            illustration_positions = [i for i in range(illustration_frequency - 1, len(pages), illustration_frequency)]

        return (pages, numbered_pages_string, illustration_positions)


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
        # Guard: detect LLM error responses and fail loudly before bad data propagates
        error_indicators = ["'error':", '"error":', "Connection closed", "Error:", "Unexpected format"]
        stripped = art_director_response.strip()
        for indicator in error_indicators:
            if indicator in stripped:
                raise RuntimeError(
                    f"[MiniBookPromptParser] LLM returned an error instead of scene prompts. "
                    f"Check your API key, model name, and OpenRouter account credits.\n"
                    f"Raw response: {stripped[:300]}"
                )

        # Extract lines starting with a number and a period (e.g. "1. ...", "2. ...")
        prompts = []
        for line in art_director_response.split('\n'):
            match = re.match(r'^\d+\.\s*(.*)', line.strip())
            if match:
                content = match.group(1).strip()
                if content:
                    prompts.append(content)
                
        if not prompts:
            raise RuntimeError(
                f"[MiniBookPromptParser] Could not parse any numbered scene prompts from art director response. "
                f"Expected format: '1. [prompt]\n2. [prompt]...'\n"
                f"Raw response (first 300 chars): {stripped[:300]}"
            )
            
        return (prompts,)
