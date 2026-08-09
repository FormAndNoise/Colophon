import torch

class InterleaveImageLists:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "images1": ("IMAGE",),
            "images2": ("IMAGE",)
        }}

    RETURN_TYPES = ("IMAGE",)
    OUTPUT_IS_LIST = (False,)
    INPUT_IS_LIST = True
    FUNCTION = "interleave"
    CATEGORY = "MiniBook"

    def interleave(self, images1, images2):
        result = []
        for first, second in zip(images1, images2):
            result.extend((first, second))
        result.extend(images1[len(images2):])
        result.extend(images2[len(images1):])
        if not result:
            raise ValueError(
                "[InterleaveImageLists] Both image lists are empty; nothing to interleave."
            )
        return (torch.cat(result, dim=0),)

# NOTE: no NODE_CLASS_MAPPINGS here — ComfyUI only discovers the mapping in
# the package root __init__.py. A local mapping was present before and was
# silently dead code (a trap for future edits).
