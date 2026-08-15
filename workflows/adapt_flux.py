import json
import os

file_path = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial.json"
output_path = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows/minibook_editorial_flux.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Find node with id 10 (CheckpointLoaderSimple)
node_10_index = next((i for i, n in enumerate(data['nodes']) if n['id'] == 10), None)
if node_10_index is not None:
    data['nodes'].pop(node_10_index)

# Create Unet Loader
unet_loader = {
    "id": 1010,
    "type": "UNETLoader",
    "pos": [99, 1350],
    "size": [300, 100],
    "flags": {},
    "order": 4,
    "mode": 0,
    "inputs": [],
    "outputs": [
        {
            "name": "MODEL",
            "type": "MODEL",
            "links": [49]
        }
    ],
    "title": "Load Diffusion Model",
    "properties": {
        "Node name for S&R": "UNETLoader"
    },
    "widgets_values": ["flux1-dev.safetensors", "default"]
}

# Create DualCLIPLoader
dual_clip_loader = {
    "id": 1011,
    "type": "DualCLIPLoader",
    "pos": [99, 1480],
    "size": [300, 135],
    "flags": {},
    "order": 5,
    "mode": 0,
    "inputs": [],
    "outputs": [
        {
            "name": "CLIP",
            "type": "CLIP",
            "links": [48, 62]
        }
    ],
    "title": "DualCLIPLoader",
    "properties": {
        "Node name for S&R": "DualCLIPLoader"
    },
    "widgets_values": ["t5xxl_fp16.safetensors", "clip_l.safetensors", "flux"]
}

# Create VAELoader
vae_loader = {
    "id": 1012,
    "type": "VAELoader",
    "pos": [99, 1650],
    "size": [300, 100],
    "flags": {},
    "order": 6,
    "mode": 0,
    "inputs": [],
    "outputs": [
        {
            "name": "VAE",
            "type": "VAE",
            "links": [60]
        }
    ],
    "title": "Load VAE",
    "properties": {
        "Node name for S&R": "VAELoader"
    },
    "widgets_values": ["ae.safetensors"]
}

# Shift EmptyLatentImage down so it doesn't overlap
for node in data['nodes']:
    if node['id'] == 13: # EmptyLatentImage
        node['pos'] = [99, 1800]
    elif node['id'] == 22: # CLIPVisionLoader
        node['pos'] = [99, 1980]
    elif node['id'] == 23: # IPAdapterInsightFaceLoader
        node['pos'] = [99, 2100]
    elif node['id'] == 50: # APIProviderSelectorNode
        node['pos'] = [99, 2300]
    elif node['id'] == 98:
        node['pos'] = [99, 2550]
    elif node['id'] == 99:
        node['pos'] = [99, 2950]
        
# Adjust KSampler settings for FLUX (typically lower CFG, different sampler/scheduler)
for node in data['nodes']:
    if node['id'] == 12: # KSampler
        # widgets: seed, control_after_generate, steps, cfg, sampler_name, scheduler, denoise
        node['widgets_values'] = [307862921549097, "randomize", 20, 1.0, "euler", "simple", 1.0]

data['nodes'].extend([unet_loader, dual_clip_loader, vae_loader])

# Update links
for link in data['links']:
    if link[0] == 49:
        link[1] = 1010
        link[2] = 0
    elif link[0] == 48:
        link[1] = 1011
        link[2] = 0
    elif link[0] == 62:
        link[1] = 1011
        link[2] = 0
    elif link[0] == 60:
        link[1] = 1012
        link[2] = 0

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, separators=(',', ':'))

print("Created minibook_editorial_flux.json")
