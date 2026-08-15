import os
import json
import glob

workflow_dir = "C:/Users/Aarik/Desktop/ComfyUI-MiniBook_Node/workflows"
json_files = glob.glob(os.path.join(workflow_dir, "*.json"))

for fp in json_files:
    try:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        modified = False
        for node in data.get("nodes", []):
            if node.get("type") == "APIProviderSelectorNode":
                node["type"] = "MiniBookLLMProvider"
                node["title"] = "LLM Provider (MiniBook)"
                if "properties" in node and "Node name for S&R" in node["properties"]:
                    node["properties"]["Node name for S&R"] = "MiniBookLLMProvider"
                modified = True
                
        if modified:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Updated: {os.path.basename(fp)}")
    except Exception as e:
        print(f"Error processing {os.path.basename(fp)}: {e}")
