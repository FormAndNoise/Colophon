"""
MiniBook Literary Editor Node
=============================
An LLM-powered editorial brain that reads a raw story and produces an intelligent
editorial plan with pagination decisions based on narrative flow, dramatic beats,
and proper book structure — not arbitrary word counts.
"""

import json
import re
from .llm_bridge import run_llm


class MiniBookLiteraryEditor:
    """
    Replaces the old MiniBookFormatter's word-count guillotine with an LLM
    that understands literary pacing, chapter structure, and visual rhythm.
    """

    BOOK_FORMATS = ["picture_book", "graphic_novel", "novella", "poetry_collection"]
    SHEET_SIZES = ["A4", "A5", "US_Letter", "US_Trade_6x9", "Square_8x8"]

    # Approximate word capacities per page for each sheet size at comfortable reading density
    WORDS_PER_PAGE_GUIDE = {
        "A4": 250,
        "A5": 150,
        "US_Letter": 250,
        "US_Trade_6x9": 200,
        "Square_8x8": 120,
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "raw_story": ("STRING", {"multiline": True, "forceInput": True}),
                "book_format": (cls.BOOK_FORMATS, {"default": "graphic_novel"}),
                "target_page_count": ("INT", {"default": 16, "min": 4, "max": 200, "step": 1}),
                "sheet_size": (cls.SHEET_SIZES, {"default": "US_Trade_6x9"}),
                "context": ("LLM_CONTEXT",),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("editorial_plan", "page_texts", "page_types")
    OUTPUT_IS_LIST = (False, True, True)
    FUNCTION = "edit"
    CATEGORY = "MiniBook"

    # ------------------------------------------------------------------
    # Core system prompt — this is the editorial intelligence
    # ------------------------------------------------------------------
    SYSTEM_PROMPT = """You are a senior literary editor and book designer with 30 years of experience 
at major publishing houses. You have an intuitive sense for pacing, page turns, 
and the visual rhythm of a printed book.

Your job is to take a raw story manuscript and produce an EDITORIAL PLAN that 
breaks the story into pages intelligently. You are NOT just splitting by word count. 
You are making editorial decisions:

1. **Dramatic Pacing**: A climactic reveal deserves its own page. Setup and payoff 
   should be separated by a page turn so the reader experiences suspense.
2. **Visual Rhythm**: Alternate between text-heavy pages and illustration pages. 
   Never stack more than 2 text-only pages in a row without a visual break.
3. **Breathing Room**: Short, punchy pages create tension. Long, flowing pages 
   create immersion. Use both deliberately.
4. **Chapter Structure**: If the story has natural chapter breaks, honor them. 
   Each chapter should start on a new page.
5. **Opening & Closing**: The first page of story text should be short and 
   impactful — a hook. The last page should land with finality.

IMPORTANT CONSTRAINTS:
- Each page's text should be readable at the given sheet size. Consult the 
  approximate word capacity provided.
- The target page count is a GUIDE, not a hard limit. You may deviate by ±20%.
- Every page MUST have a type tag. Valid types are:
  - "text_only" — Pure text, no illustration
  - "text_with_illustration" — Text on one portion, illustration on the other
  - "full_illustration" — Full-page illustration with optional short caption
  - "chapter_opener" — Decorative page with chapter title and opening text
  - "section_break" — A visual pause (could be a divider or short epigraph)

Respond with ONLY valid JSON in this exact structure:
{
  "title": "The story's title (infer from content if not explicit)",
  "total_pages": <int>,
  "editorial_notes": "Brief notes on your pacing decisions",
  "pages": [
    {
      "page_number": 1,
      "type": "chapter_opener",
      "text": "The actual text content for this page",
      "illustration_note": "Brief description of what illustration would complement this page, or null",
      "pacing_note": "Why you made this editorial choice"
    }
  ]
}"""

    def _build_user_prompt(self, raw_story, book_format, target_page_count, sheet_size):
        words_capacity = self.WORDS_PER_PAGE_GUIDE.get(sheet_size, 200)
        word_count = len(raw_story.split())

        return f"""Here is the manuscript to edit and paginate:

--- MANUSCRIPT START ---
{raw_story}
--- MANUSCRIPT END ---

PRODUCTION SPECIFICATIONS:
- Book format: {book_format}
- Target page count: {target_page_count} pages (±20% is acceptable)
- Sheet size: {sheet_size}
- Approximate word capacity per text page: {words_capacity} words
- Total manuscript word count: {word_count} words

Please produce the editorial plan as specified. Remember: you are an editor, 
not a word processor. Make choices that serve the story."""

    def _deterministic_fallback(self, raw_story, sheet_size, target_page_count):
        words_capacity = self.WORDS_PER_PAGE_GUIDE.get(sheet_size, 200)
        words = raw_story.split()
        
        pages = []
        page_num = 1
        
        words_per_page = min(words_capacity, max(30, len(words) // target_page_count))
        
        for i in range(0, len(words), words_per_page):
            chunk = " ".join(words[i:i+words_per_page])
            pages.append({
                "page_number": page_num,
                "type": "text_with_illustration" if page_num % 2 != 0 else "text_only",
                "text": chunk,
                "illustration_note": "A scene from the story" if page_num % 2 != 0 else None,
                "pacing_note": "Fallback splitting"
            })
            page_num += 1
            
        return {
            "title": "Untitled",
            "total_pages": len(pages),
            "editorial_notes": "Fallback deterministic splitting",
            "pages": pages
        }

    def _salvage_truncated_plan(self, cleaned):
        """
        Recover from a response that got cut off by max_tokens mid-page.
        Strategy: find the last complete page object inside "pages": [...],
        drop everything after it, close the array and object, then parse.
        Returns a plan dict or None if unsalvageable.
        """
        pages_key = cleaned.find('"pages"')
        if pages_key == -1:
            return None
        arr_start = cleaned.find('[', pages_key)
        if arr_start == -1:
            return None

        # Walk the pages array and remember the position AFTER the last
        # balanced page object (depth returns to 0 inside the array).
        depth = 0
        in_string = False
        escape = False
        last_good_close = -1
        for i in range(arr_start + 1, len(cleaned)):
            ch = cleaned[i]
            if escape:
                escape = False
                continue
            if ch == '\\' and in_string:
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    last_good_close = i  # position of the closing brace of a page object

        if last_good_close == -1:
            return None

        repaired = cleaned[:last_good_close + 1] + "]}"
        try:
            plan = json.loads(repaired)
            print(f"[MiniBookLiteraryEditor] Recovered truncated editorial plan "
                  f"(kept {len(plan.get('pages', []))} complete pages).")
            return plan
        except json.JSONDecodeError:
            return None

    def _parse_editorial_plan(self, llm_response):
        """
        Parse the LLM's JSON response into structured data.
        Handles common LLM quirks like markdown code fences around JSON,
        and salvages plans that were truncated mid-page by max_tokens.
        """
        # Strip markdown code fences if present
        cleaned = llm_response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        plan = None
        parse_error = None
        try:
            plan = json.loads(cleaned)
        except json.JSONDecodeError as e:
            parse_error = e
            # Try to extract JSON from within the response
            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                try:
                    plan = json.loads(json_match.group())
                except json.JSONDecodeError:
                    plan = None

        if plan is None:
            # Last-chance salvage: response likely truncated by max_tokens.
            plan = self._salvage_truncated_plan(cleaned)

        if plan is None:
            if parse_error is not None:
                raise RuntimeError(
                    f"[MiniBookLiteraryEditor] Could not parse editorial plan JSON. "
                    f"Parse error: {parse_error}\nRaw response (first 500 chars): {cleaned[:500]}"
                )
            raise RuntimeError(
                f"[MiniBookLiteraryEditor] LLM did not return valid JSON. "
                f"Raw response (first 500 chars): {cleaned[:500]}"
            )

        # Validate required structure
        if "pages" not in plan or not isinstance(plan["pages"], list):
            raise RuntimeError(
                "[MiniBookLiteraryEditor] Editorial plan missing 'pages' array."
            )

        if len(plan["pages"]) == 0:
            raise RuntimeError(
                "[MiniBookLiteraryEditor] Editorial plan has zero pages."
            )

        return plan

    def edit(self, raw_story, book_format, target_page_count, sheet_size, context):
        """Main execution: send story to LLM editor, parse results, return structured output."""

        # Guard against bad input
        stripped = raw_story.strip()
        if len(stripped) < 50:
            raise RuntimeError(
                f"[MiniBookLiteraryEditor] Story text is too short to edit ({len(stripped)} chars)."
            )

        error_indicators = ["'error':", '"error":', "Connection closed"]
        for indicator in error_indicators:
            if indicator in stripped:
                raise RuntimeError(
                    f"[MiniBookLiteraryEditor] Received an error response instead of story text. "
                    f"Raw: {stripped[:300]}"
                )

        # Build prompts and call the LLM.
        # 16k tokens is enough for ~40+ pages of embedded text in strict JSON,
        # well above the toolkit's stingy 2048-token default that was truncating
        # the plan mid-page.
        user_prompt = self._build_user_prompt(raw_story, book_format, target_page_count, sheet_size)
        try:
            llm_response = run_llm(context, self.SYSTEM_PROMPT, user_prompt, max_tokens=16384)
            plan = self._parse_editorial_plan(llm_response)
        except Exception as e:
            print(f"[MiniBookLiteraryEditor] LLM pagination failed: {e}. Falling back to deterministic word-count splitter.")
            plan = self._deterministic_fallback(raw_story, sheet_size, target_page_count)

        # Extract page texts and types
        page_texts = []
        page_types = []
        valid_types = {
            "text_only", "text_with_illustration", "full_illustration",
            "chapter_opener", "section_break"
        }

        for page in plan["pages"]:
            text = page.get("text", "").strip()
            page_type = page.get("type", "text_only").strip()

            # Normalize and validate page type
            if page_type not in valid_types:
                page_type = "text_only"

            page_texts.append(text)
            page_types.append(page_type)

        # Serialize the full plan as a JSON string for downstream nodes
        editorial_plan_json = json.dumps(plan, indent=2, ensure_ascii=False)

        return (editorial_plan_json, page_texts, page_types)
