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
            if node.get("type") == "FL_ImageListToImageBatch":
                node["type"] = "MiniBookImageListToBatch"
                node["title"] = "List to Batch (MiniBook)"
                if "properties" in node and "Node name for S&R" in node["properties"]:
                    node["properties"]["Node name for S&R"] = "MiniBookImageListToBatch"
                modified = True
            elif node.get("type") == "FL_ImagesToPDF":
                node["type"] = "MiniBookImagesToPDF"
                node["title"] = "PDF Compiler (MiniBook)"
                if "properties" in node and "Node name for S&R" in node["properties"]:
                    node["properties"]["Node name for S&R"] = "MiniBookImagesToPDF"
                modified = True
            elif node.get("type") == "FL_PDFSaver":
                node["type"] = "MiniBookPDFSaver"
                node["title"] = "PDF Saver (MiniBook)"
                if "properties" in node and "Node name for S&R" in node["properties"]:
                    node["properties"]["Node name for S&R"] = "MiniBookPDFSaver"
                modified = True
                
        if modified:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Updated: {os.path.basename(fp)}")
    except Exception as e:
        print(f"Error processing {os.path.basename(fp)}: {e}")
