import torch

class InterleaveImageLists:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "images1": ("IMAGE",),
            "images2": ("IMAGE",)
        }}
    
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_IS_LIST = (True,)
    INPUT_IS_LIST = True
    FUNCTION = "interleave"
    CATEGORY = "MiniBook"
    
    def interleave(self, images1, images2):
        result = []
        min_len = min(len(images1), len(images2))
        for i in range(min_len):
            result.append(images1[i])
            result.append(images2[i])
        return (result,)

NODE_CLASS_MAPPINGS = {
    "InterleaveImageLists": InterleaveImageLists
}
