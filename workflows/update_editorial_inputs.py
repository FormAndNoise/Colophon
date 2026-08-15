import json
import os

file_path = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for node in data.get("nodes", []):
    if node.get("type") == "MiniBookStoryInputs":
        # Modify the widgets_values
        # 0: format, 1: theme, 2: art_style, 3: constraints, 4: character_description
        node["widgets_values"] = [
            "A cozy, lighthearted fantasy picture book for all ages.",
            "A grumpy but talented goblin baker who accidentally bakes a batch of sentient, overly-affectionate bread loaves that refuse to be eaten and instead want to help him run his struggling bakery.",
            "warm studio ghibli inspired, soft watercolor textures, golden hour lighting, cozy cluttered bakery interiors, rustic charm.",
            "The tone should be heartwarming and comedic. Focus heavily on the sensory details of baking (the smell of yeast, warmth of the oven, flour dust in the air). Keep it wholesome with zero scary elements.",
            "Barnaby: A stout, green-skinned goblin wearing a messy baker's apron, with flour on his nose and a permanent scowl. The Loaves: Plump, golden-brown bread loaves with simple, happy expressions."
        ]
        break

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("minibook_editorial.json updated with Cozy Fantasy inputs!")
