import random
import re
from .llm_bridge import run_llm

class MiniBookMadLibsEngine:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "theme": ("STRING", {"multiline": True, "forceInput": True}),
                "nouns": ("STRING", {"multiline": True, "default": "banana, politician, toilet, noodle"}),
                "verbs": ("STRING", {"multiline": True, "default": "slapped, regurgitated, exploded, tickled"}),
                "adjectives": ("STRING", {"multiline": True, "default": "slimy, radioactive, depressed, crunchy"}),
                "context": ("LLM_CONTEXT",),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("madlib_story",)
    FUNCTION = "generate"
    CATEGORY = "MiniBook"
    
    def generate(self, theme, nouns, verbs, adjectives, context):
        noun_list = [w.strip() for w in nouns.split(',') if w.strip()]
        verb_list = [w.strip() for w in verbs.split(',') if w.strip()]
        adj_list = [w.strip() for w in adjectives.split(',') if w.strip()]
        
        prompt = f"""Write a short, engaging story based on the instructions: '{theme}'. 
The catch: You must leave exactly {len(noun_list)} blanks for nouns by writing [NOUN], {len(verb_list)} blanks for verbs by writing [VERB], and {len(adj_list)} blanks for adjectives by writing [ADJECTIVE].
Choose provocative, important, or funny places in the sentence to put these blanks, so that when filled with random words, it becomes nonsensical and hilarious.
Do NOT fill the blanks in yourself. Output ONLY the story text."""
        
        raw_story = run_llm(context, "You are a witty Mad Libs story author.", prompt, max_tokens=2048)
        
        # Replace the placeholders with the words, in ALL CAPS to highlight them
        random.shuffle(noun_list)
        random.shuffle(verb_list)
        random.shuffle(adj_list)
        
        def replacer_noun(match):
            return noun_list.pop().upper() if noun_list else "[NOUN]"
        def replacer_verb(match):
            return verb_list.pop().upper() if verb_list else "[VERB]"
        def replacer_adj(match):
            return adj_list.pop().upper() if adj_list else "[ADJECTIVE]"
            
        story = re.sub(r'\[NOUN\]', replacer_noun, raw_story, flags=re.IGNORECASE)
        story = re.sub(r'\[VERB\]', replacer_verb, story, flags=re.IGNORECASE)
        story = re.sub(r'\[ADJECTIVE\]', replacer_adj, story, flags=re.IGNORECASE)
        
        return (story,)

