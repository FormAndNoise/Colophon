import os
import json
import glob

workflow_dir = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows"
json_files = glob.glob(os.path.join(workflow_dir, "*.json"))

for fp in json_files:
    try:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        nodes = data.get("nodes", [])
        links = data.get("links", [])
        
        # Find MasterBookControl node
        master_node = next((n for n in nodes if n["type"] == "MasterBookControl"), None)
        if not master_node:
            continue
            
        master_id = master_node["id"]
        
        # Find links connected to MasterBookControl
        # link format: [id, origin_id, origin_slot, target_id, target_slot, type]
        input_links = {link[4]: link for link in links if link[3] == master_id}
        
        # Slots for MasterBookControl:
        # 0: format, 1: theme, 2: constraints, 3: art_style, 4: character_description
        
        # Extract values
        values = {
            "format": "word dense adult level reading novel.",
            "theme": "",
            "constraints": "",
            "art_style": "futuristic art nouveau in monochrome",
            "character_description": ""
        }
        
        nodes_to_remove = set()
        
        for slot, key in enumerate(["format", "theme", "constraints", "art_style", "character_description"]):
            if slot in input_links:
                link = input_links[slot]
                origin_id = link[1]
                origin_node = next((n for n in nodes if n["id"] == origin_id), None)
                if origin_node and origin_node["type"] == "TextInput":
                    nodes_to_remove.add(origin_id)
                    # The text is usually in widgets_values[4]
                    if len(origin_node.get("widgets_values", [])) > 4:
                        values[key] = origin_node["widgets_values"][4]
                        
        if not nodes_to_remove:
            continue # already processed or doesn't use TextInput nodes
            
        # Create new MiniBookStoryInputs node
        new_node_id = max([n["id"] for n in nodes]) + 1
        new_node = {
            "id": new_node_id,
            "type": "MiniBookStoryInputs",
            "pos": [99, 126], # old pos of theme
            "size": [400, 300],
            "flags": {},
            "order": 0,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "format", "type": "STRING", "links": []},
                {"name": "theme", "type": "STRING", "links": []},
                {"name": "art_style", "type": "STRING", "links": []},
                {"name": "constraints", "type": "STRING", "links": []},
                {"name": "character_description", "type": "STRING", "links": []}
            ],
            "title": "Story Inputs (MiniBook)",
            "properties": {"Node name for S&R": "MiniBookStoryInputs"},
            "widgets_values": [
                values["format"],
                values["theme"],
                values["art_style"],
                values["constraints"],
                values["character_description"]
            ]
        }
        
        # Update links
        # MiniBookStoryInputs outputs: 0: format, 1: theme, 2: art_style, 3: constraints, 4: character_description
        slot_mapping = {0: 0, 1: 1, 2: 3, 3: 2, 4: 4} # master_slot : new_node_slot
        
        for slot in range(5):
            if slot in input_links:
                link = input_links[slot]
                link[1] = new_node_id
                link[2] = slot_mapping[slot]
                new_node["outputs"][slot_mapping[slot]]["links"].append(link[0])
                
        # Remove old nodes
        data["nodes"] = [n for n in nodes if n["id"] not in nodes_to_remove]
        data["nodes"].insert(0, new_node)
        
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        print(f"Compressed inputs in {os.path.basename(fp)}")
        
    except Exception as e:
        import traceback
        print(f"Error processing {os.path.basename(fp)}: {e}")
        traceback.print_exc()
