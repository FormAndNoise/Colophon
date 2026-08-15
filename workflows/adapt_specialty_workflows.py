import json
import os
import copy

file_path = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial.json"

with open(file_path, "r", encoding="utf-8") as f:
    original_data = json.load(f)

def remove_node(data, node_id):
    data['nodes'] = [n for n in data['nodes'] if n['id'] != node_id]
    data['links'] = [l for l in data['links'] if l[1] != node_id and l[3] != node_id]

def add_link(data, from_node, from_socket, to_node, to_socket, link_type="*"):
    max_link = max([l[0] for l in data['links']]) if data['links'] else 0
    new_link_id = max_link + 1
    data['links'].append([new_link_id, from_node, from_socket, to_node, to_socket, link_type])
    for n in data['nodes']:
        if n['id'] == to_node:
            if 'inputs' in n:
                if to_socket < len(n['inputs']):
                    n['inputs'][to_socket]['link'] = new_link_id
            break
    for n in data['nodes']:
        if n['id'] == from_node:
            if 'outputs' in n:
                if from_socket < len(n['outputs']):
                    if n['outputs'][from_socket]['links'] is None:
                        n['outputs'][from_socket]['links'] = []
                    n['outputs'][from_socket]['links'].append(new_link_id)
            break
    return new_link_id

# 1. Early Reader
early = copy.deepcopy(original_data)
remove_node(early, 5) # Remove LLM Generator
early['nodes'].append({
    "id": 500, "type": "MiniBookEarlyReaderGenerator", "pos": [1044, 585], "size": [400, 250], "flags": {}, "order": 15, "mode": 0,
    "inputs": [
        {"name": "theme", "type": "STRING", "link": None},
        {"name": "reading_level", "type": "COMBO", "widget": {"name": "reading_level"}, "link": None},
        {"name": "target_vocabulary", "type": "STRING", "widget": {"name": "target_vocabulary"}, "link": None},
        {"name": "context", "type": "LLM_CONTEXT", "link": None}
    ],
    "outputs": [{"name": "raw_story", "type": "STRING", "links": []}],
    "title": "Early Reader Generator", "properties": {"Node name for S&R": "MiniBookEarlyReaderGenerator"},
    "widgets_values": ["Kindergarten (CVC)", "cat, sat, mat, hat"]
})
add_link(early, 4, 0, 500, 0, "STRING") # theme
add_link(early, 50, 0, 500, 3, "LLM_CONTEXT") # context
add_link(early, 500, 0, 600, 0, "STRING") # output to editor
add_link(early, 500, 0, 630, 1, "STRING") # output to front matter
with open("C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial_early_reader.json", "w", encoding="utf-8") as f:
    json.dump(early, f, indent=2)

# 2. Bilingual
bilin = copy.deepcopy(original_data)
remove_node(bilin, 5)
bilin['nodes'].append({
    "id": 500, "type": "MiniBookBilingualGenerator", "pos": [1044, 585], "size": [400, 250], "flags": {}, "order": 15, "mode": 0,
    "inputs": [
        {"name": "theme", "type": "STRING", "link": None},
        {"name": "primary_language", "type": "STRING", "widget": {"name": "primary_language"}, "link": None},
        {"name": "secondary_language", "type": "STRING", "widget": {"name": "secondary_language"}, "link": None},
        {"name": "context", "type": "LLM_CONTEXT", "link": None}
    ],
    "outputs": [{"name": "raw_story", "type": "STRING", "links": []}],
    "title": "Bilingual Book Generator", "properties": {"Node name for S&R": "MiniBookBilingualGenerator"},
    "widgets_values": ["English", "Spanish"]
})
add_link(bilin, 4, 0, 500, 0, "STRING")
add_link(bilin, 50, 0, 500, 3, "LLM_CONTEXT")
add_link(bilin, 500, 0, 600, 0, "STRING")
add_link(bilin, 500, 0, 630, 1, "STRING")
with open("C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial_bilingual.json", "w", encoding="utf-8") as f:
    json.dump(bilin, f, indent=2)

# 3. Workbook
workb = copy.deepcopy(original_data)
remove_node(workb, 5)
workb['nodes'].append({
    "id": 500, "type": "MiniBookWorkbookGenerator", "pos": [1044, 585], "size": [400, 250], "flags": {}, "order": 15, "mode": 0,
    "inputs": [
        {"name": "topic", "type": "STRING", "link": None},
        {"name": "num_exercises", "type": "INT", "widget": {"name": "num_exercises"}, "link": None},
        {"name": "context", "type": "LLM_CONTEXT", "link": None}
    ],
    "outputs": [{"name": "raw_story", "type": "STRING", "links": []}],
    "title": "Workbook Generator", "properties": {"Node name for S&R": "MiniBookWorkbookGenerator"},
    "widgets_values": [10]
})
add_link(workb, 4, 0, 500, 0, "STRING")
add_link(workb, 50, 0, 500, 2, "LLM_CONTEXT")
add_link(workb, 500, 0, 600, 0, "STRING")
add_link(workb, 500, 0, 630, 1, "STRING")
for n in workb['nodes']:
    if n['id'] == 3: n['widgets_values'][4] = "peaceful, abstract watercolor, soft pastels, calming, zen, minimalist"
with open("C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial_workbook.json", "w", encoding="utf-8") as f:
    json.dump(workb, f, indent=2)

# 4. CYOA (uses Structured workflow logic)
cyoa = copy.deepcopy(original_data)
nodes_to_remove = [5, 600, 610, 620, 630, 640]
for nid in nodes_to_remove:
    remove_node(cyoa, nid)
cyoa['links'] = [l for l in cyoa['links'] if l[3] != 101]
for n in cyoa['nodes']:
    if n['id'] == 101:
        for inp in n.get('inputs', []):
            inp['link'] = None

cyoa['nodes'].extend([
    {
        "id": 500, "type": "MiniBookCYOAGenerator", "pos": [1044, 585], "size": [400, 250], "flags": {}, "order": 15, "mode": 0,
        "inputs": [
            {"name": "theme", "type": "STRING", "link": None},
            {"name": "num_pages", "type": "INT", "widget": {"name": "num_pages"}, "link": None},
            {"name": "context", "type": "LLM_CONTEXT", "link": None}
        ],
        "outputs": [
            {"name": "page_texts", "type": "STRING", "links": []},
            {"name": "scene_prompts", "type": "STRING", "links": []}
        ],
        "title": "CYOA Book Generator", "properties": {"Node name for S&R": "MiniBookCYOAGenerator"},
        "widgets_values": [12]
    },
    {
        "id": 505, "type": "EmptyLatentImage", "pos": [1500, 700], "size": [270, 144], "flags": {}, "order": 17, "mode": 0,
        "inputs": [], "outputs": [{"name": "LATENT", "type": "LATENT", "links": []}],
        "title": "Text Page Background", "properties": {"Node name for S&R": "EmptyLatentImage"},
        "widgets_values": [1024, 1032, 1]
    },
    {
        "id": 506, "type": "VAEDecode", "pos": [1800, 700], "size": [225, 72], "flags": {}, "order": 18, "mode": 0,
        "inputs": [{"name": "samples", "type": "LATENT", "link": None}, {"name": "vae", "type": "VAE", "link": None}],
        "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}],
        "title": "Decode Background", "properties": {"Node name for S&R": "VAEDecode"},
        "widgets_values": []
    },
    {
        "id": 502, "type": "BTTextToImage", "pos": [1900, 500], "size": [300, 400], "flags": {}, "order": 19, "mode": 0,
        "inputs": [
            {"name": "image", "type": "IMAGE", "link": None},
            {"name": "text", "type": "STRING", "link": None}
        ],
        "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}],
        "title": "Render Text Pages", "properties": {"Node name for S&R": "BTTextToImage"},
        "widgets_values": [64, 24, "default", 40, 1.4, 0.0, 0.2, False, 20, 4, 3, False, "vertical", "none", "auto", 20, "left", "center", "random"]
    },
    {
        "id": 503, "type": "InterleaveImageLists", "pos": [3300, 126], "size": [300, 150], "flags": {}, "order": 24, "mode": 0,
        "inputs": [
            {"name": "images1", "type": "IMAGE", "link": None},
            {"name": "images2", "type": "IMAGE", "link": None}
        ],
        "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}],
        "title": "Interleave Text & Illustrations", "properties": {"Node name for S&R": "InterleaveImageLists"},
        "widgets_values": []
    }
])

add_link(cyoa, 4, 0, 500, 0, "STRING") # Theme
add_link(cyoa, 50, 0, 500, 2, "LLM_CONTEXT") # Context

# 500(1) scene_prompts -> 7(1) Positive Prompt
add_link(cyoa, 500, 1, 7, 1, "STRING")
# 500(0) page_texts -> 502(1) Text to image
add_link(cyoa, 500, 0, 502, 1, "STRING")

add_link(cyoa, 505, 0, 506, 0, "LATENT")
add_link(cyoa, 10, 2, 506, 1, "VAE")
add_link(cyoa, 506, 0, 502, 0, "IMAGE")

add_link(cyoa, 502, 0, 503, 0, "IMAGE") # texts
add_link(cyoa, 14, 0, 503, 1, "IMAGE") # illustrations

add_link(cyoa, 503, 0, 101, 0, "IMAGE")

with open("C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial_cyoa.json", "w", encoding="utf-8") as f:
    json.dump(cyoa, f, indent=2)

print("Created 4 specialty workflows")
