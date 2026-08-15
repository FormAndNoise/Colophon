import torch
import numpy as np
from PIL import Image
import os
import io

class MiniBookImageListToBatch:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"images": ("IMAGE",)}}

    INPUT_IS_LIST = True
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "execute"
    CATEGORY = "MiniBook"

    def execute(self, images):
        if not images:
            return (torch.empty(0),)
        return (torch.cat(images, dim=0),)


class MiniBookImagesToPDF:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "dpi": ("INT", {"default": 300, "min": 72, "max": 1200}),
                "page_size": (["A4", "US_Letter", "Custom"], {"default": "A4"}),
            }
        }
        
    RETURN_TYPES = ("PDF",)
    FUNCTION = "execute"
    CATEGORY = "MiniBook"

    def execute(self, images, dpi, page_size):
        pil_images = []
        for i in range(images.shape[0]):
            img = images[i].cpu().numpy()
            img = (img * 255.0).clip(0, 255).astype(np.uint8)
            pil_images.append(Image.fromarray(img))
            
        if not pil_images:
            return (None,)
            
        pdf_bytes = io.BytesIO()
        pil_images[0].save(
            pdf_bytes,
            "PDF",
            resolution=dpi,
            save_all=True,
            append_images=pil_images[1:]
        )
        return (pdf_bytes.getvalue(),)


class MiniBookPDFSaver:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pdf": ("PDF",),
                "output_directory": ("STRING", {"default": "output"}),
                "filename": ("STRING", {"default": "minibook_output"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)
    FUNCTION = "execute"
    OUTPUT_NODE = True
    CATEGORY = "MiniBook"

    def execute(self, pdf, output_directory, filename):
        if not pdf:
            return ("No PDF to save",)
            
        try:
            import folder_paths
            base_dir = folder_paths.get_output_directory()
        except Exception:
            base_dir = os.path.abspath("output")
            
        if not os.path.isabs(output_directory):
            save_dir = os.path.join(base_dir, output_directory)
        else:
            save_dir = output_directory
            
        os.makedirs(save_dir, exist_ok=True)
        
        counter = 1
        file_path = os.path.join(save_dir, f"{filename}_{counter:05d}.pdf")
        while os.path.exists(file_path):
            counter += 1
            file_path = os.path.join(save_dir, f"{filename}_{counter:05d}.pdf")
            
        with open(file_path, "wb") as f:
            f.write(pdf)
            
        print(f"[MiniBook] PDF saved to {file_path}")
        return (file_path,)
