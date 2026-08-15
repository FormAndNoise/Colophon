import json
import os
import copy

file_path = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial.json"

with open(file_path, "r", encoding="utf-8") as f:
    original_data = json.load(f)

def get_max_id(data):
    max_node = max([n['id'] for n in data['nodes']]) if data['nodes'] else 0
    max_link = max([l[0] for l in data['links']]) if data['links'] else 0
    return max_node, max_link

def remove_node(data, node_id):
    data['nodes'] = [n for n in data['nodes'] if n['id'] != node_id]
    data['links'] = [l for l in data['links'] if l[1] != node_id and l[3] != node_id]

def replace_link(data, old_from_id, new_from_id, new_from_socket=0):
    for l in data['links']:
        if l[1] == old_from_id:
            l[1] = new_from_id
            l[2] = new_from_socket

def add_link(data, from_node, from_socket, to_node, to_socket, link_type="*"):
    max_link = max([l[0] for l in data['links']]) if data['links'] else 0
    new_link_id = max_link + 1
    data['links'].append([new_link_id, from_node, from_socket, to_node, to_socket, link_type])
    
    # Update to_node inputs
    for n in data['nodes']:
        if n['id'] == to_node:
            # find which input this corresponds to
            if 'inputs' in n:
                if to_socket < len(n['inputs']):
                    n['inputs'][to_socket]['link'] = new_link_id
            break
    
    # Update from_node outputs
    for n in data['nodes']:
        if n['id'] == from_node:
            if 'outputs' in n:
                if from_socket < len(n['outputs']):
                    if n['outputs'][from_socket]['links'] is None:
                        n['outputs'][from_socket]['links'] = []
                    n['outputs'][from_socket]['links'].append(new_link_id)
            break
    return new_link_id

# ---------------------------------------------------------
# WORKFLOW 1: RAW TEXT INPUT
# ---------------------------------------------------------
raw_data = copy.deepcopy(original_data)

# Remove LLM Toolkit Node
remove_node(raw_data, 5)

# Add TextInput for Raw Manuscript
text_input_raw = {
    "id": 500,
    "type": "TextInput",
    "pos": [1044, 585],
    "size": [400, 300],
    "flags": {},
    "order": 15,
    "mode": 0,
    "inputs": [],
    "outputs": [{"name": "STRING", "type": "STRING", "links": []}],
    "title": "Raw Manuscript Input",
    "properties": {"Node name for S&R": "TextInput"},
    "widgets_values": [" ", "", "", "", "Paste your raw manuscript text here...", "", "", ""]
}
raw_data['nodes'].append(text_input_raw)

add_link(raw_data, 500, 0, 600, 0, "STRING") # to MiniBookLiteraryEditor raw_story
add_link(raw_data, 500, 0, 630, 1, "STRING") # to MiniBookFrontMatter raw_story

output_raw = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial_raw_text.json"
with open(output_raw, "w", encoding="utf-8") as f:
    json.dump(raw_data, f, indent=2)


# ---------------------------------------------------------
# WORKFLOW 2: STRUCTURED DOCUMENT INPUT
# ---------------------------------------------------------
struct_data = copy.deepcopy(original_data)

nodes_to_remove = [5, 600, 610, 620, 630, 640] # LLM, Editor, ArtDirector, Compositor, FrontMatter, Assembler
for nid in nodes_to_remove:
    remove_node(struct_data, nid)

# Disconnect the old links that went into those nodes
# Actually remove_node already removed those links.
# We also need to remove any dangling links going into Node 101 if it was from 640
struct_data['links'] = [l for l in struct_data['links'] if l[3] != 101]
# Clear inputs on Node 101
for n in struct_data['nodes']:
    if n['id'] == 101:
        for inp in n.get('inputs', []):
            inp['link'] = None

text_input_struct = {
    "id": 500,
    "type": "TextInput",
    "pos": [1000, 500],
    "size": [400, 300],
    "flags": {},
    "order": 15,
    "mode": 0,
    "inputs": [],
    "outputs": [{"name": "STRING", "type": "STRING", "links": []}],
    "title": "Structured Document Input",
    "properties": {"Node name for S&R": "TextInput"},
    "widgets_values": [" ", "", "", "", "Paste your structured document text here. Use [PAGE 1], [SCENE 1] tags.", "", "", ""]
}

text_parser = {
    "id": 501,
    "type": "MiniBookTextParser",
    "pos": [1500, 500],
    "size": [300, 100],
    "flags": {},
    "order": 16,
    "mode": 0,
    "inputs": [{"name": "text", "type": "STRING", "link": None}],
    "outputs": [
        {"name": "page_texts", "type": "STRING", "links": []},
        {"name": "scene_prompts", "type": "STRING", "links": []}
    ],
    "title": "Text Parser",
    "properties": {"Node name for S&R": "MiniBookTextParser"},
    "widgets_values": []
}

# Provide an EmptyLatentImage and VAEDecode to generate background image for text
empty_latent = {
    "id": 505,
    "type": "EmptyLatentImage",
    "pos": [1500, 700],
    "size": [270, 144],
    "flags": {},
    "order": 17,
    "mode": 0,
    "inputs": [],
    "outputs": [{"name": "LATENT", "type": "LATENT", "links": []}],
    "title": "Text Page Background",
    "properties": {"Node name for S&R": "EmptyLatentImage"},
    "widgets_values": [1024, 1032, 1]
}

vae_decode_bg = {
    "id": 506,
    "type": "VAEDecode",
    "pos": [1800, 700],
    "size": [225, 72],
    "flags": {},
    "order": 18,
    "mode": 0,
    "inputs": [{"name": "samples", "type": "LATENT", "link": None}, {"name": "vae", "type": "VAE", "link": None}],
    "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}],
    "title": "Decode Background",
    "properties": {"Node name for S&R": "VAEDecode"},
    "widgets_values": []
}

text_to_image = {
    "id": 502,
    "type": "BTTextToImage",
    "pos": [1900, 500],
    "size": [300, 400],
    "flags": {},
    "order": 19,
    "mode": 0,
    "inputs": [
        {"name": "image", "type": "IMAGE", "link": None},
        {"name": "text", "type": "STRING", "link": None}
    ],
    "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}],
    "title": "Render Text Pages",
    "properties": {"Node name for S&R": "BTTextToImage"},
    "widgets_values": [
        96, 32, "default", 40, 1.4, 0.0, 0.2, False, 20, 4, 3, False, "vertical", "none", "auto", 20, "left", "center", "random"
    ]
}

interleave = {
    "id": 503,
    "type": "InterleaveImageLists",
    "pos": [3300, 126],
    "size": [300, 150],
    "flags": {},
    "order": 24,
    "mode": 0,
    "inputs": [
        {"name": "images1", "type": "IMAGE", "link": None},
        {"name": "images2", "type": "IMAGE", "link": None}
    ],
    "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}],
    "title": "Interleave Text & Illustrations",
    "properties": {"Node name for S&R": "InterleaveImageLists"},
    "widgets_values": []
}

struct_data['nodes'].extend([text_input_struct, text_parser, empty_latent, vae_decode_bg, text_to_image, interleave])

# Connections for structured workflow:
# 500(0) -> 501(0) (text)
add_link(struct_data, 500, 0, 501, 0, "STRING")

# 501(1) (scene_prompts) -> 7(1) (text for CLIPTextEncode)
# (In original, node 7 is CLIPTextEncode Positive Prompt)
# Node 7 inputs: 0 is clip, 1 is text
add_link(struct_data, 501, 1, 7, 1, "STRING")

# 501(0) (page_texts) -> 502(1) (text)
add_link(struct_data, 501, 0, 502, 1, "STRING")

# 505(0) -> 506(0)
add_link(struct_data, 505, 0, 506, 0, "LATENT")
# 10(2) (VAE) -> 506(1)
add_link(struct_data, 10, 2, 506, 1, "VAE")
# 506(0) -> 502(0) (image)
add_link(struct_data, 506, 0, 502, 0, "IMAGE")

# Interleave inputs
# 502(0) (text images) -> 503(0) (images1)
add_link(struct_data, 502, 0, 503, 0, "IMAGE")
# 14(0) (generated illustrations) -> 503(1) (images2)
add_link(struct_data, 14, 0, 503, 1, "IMAGE")

# Interleave output to 101(0) (FL_ImageListToImageBatch)
add_link(struct_data, 503, 0, 101, 0, "IMAGE")

output_struct = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial_structured.json"
with open(output_struct, "w", encoding="utf-8") as f:
    json.dump(struct_data, f, indent=2)

print("Created minibook_editorial_raw_text.json and minibook_editorial_structured.json")
