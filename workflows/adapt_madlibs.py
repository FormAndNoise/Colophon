import json
import os
import copy

file_path = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial.json"
output_path = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial_madlibs.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

def get_max_id(data):
    max_node = max([n['id'] for n in data['nodes']]) if data['nodes'] else 0
    max_link = max([l[0] for l in data['links']]) if data['links'] else 0
    return max_node, max_link

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

# Remove the default LLM Story Generator (Node 5)
remove_node(data, 5)

# MadLibs Node definition
madlibs_node = {
    "id": 500,
    "type": "MiniBookMadLibsEngine",
    "pos": [1044, 585],
    "size": [400, 300],
    "flags": {},
    "order": 15,
    "mode": 0,
    "inputs": [
        {"name": "theme", "type": "STRING", "link": None},
        {"name": "nouns", "type": "STRING", "widget": {"name": "nouns"}, "link": None},
        {"name": "verbs", "type": "STRING", "widget": {"name": "verbs"}, "link": None},
        {"name": "adjectives", "type": "STRING", "widget": {"name": "adjectives"}, "link": None},
        {"name": "context", "type": "LLM_CONTEXT", "link": None}
    ],
    "outputs": [{"name": "madlib_story", "type": "STRING", "links": []}],
    "title": "MadLibs Story Engine",
    "properties": {"Node name for S&R": "MiniBookMadLibsEngine"},
    "widgets_values": [
        "banana, politician, toilet, noodle, submarine, sock, grandmother",
        "slapped, regurgitated, exploded, tickled, somersaulted, evaporated",
        "slimy, radioactive, depressed, crunchy, invisible, flamboyant"
    ]
}

data['nodes'].append(madlibs_node)

# Link Master Book Control Prompt (Node 4 Output 0) to MadLibs 'theme' (Input 0)
add_link(data, 4, 0, 500, 0, "STRING")

# Link APIProviderSelectorNode (Node 50 Output 0) to MadLibs 'context' (Input 4)
add_link(data, 50, 0, 500, 4, "LLM_CONTEXT")

# Link MadLibs Output to Literary Editor (Node 600 Input 0)
add_link(data, 500, 0, 600, 0, "STRING")

# Link MadLibs Output to Front Matter (Node 630 Input 1)
add_link(data, 500, 0, 630, 1, "STRING")

# Update Art Style in MasterBookControl or Node 3 to be caricaturish
for n in data['nodes']:
    if n['id'] == 3: # Art Style input node
        n['widgets_values'][4] = "caricaturish, mad magazine style, exaggerated cartoon, nonsensical, funny, vibrant colors"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Created minibook_editorial_madlibs.json")
