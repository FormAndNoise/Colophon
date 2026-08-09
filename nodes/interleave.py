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
        min_len = min(len(images1), len(images2))
        for i in range(min_len):
            result.append(images1[i])
            result.append(images2[i])
        # Stack all tensors into a single batch tensor (N, H, W, C).
        # If the lists are empty, return an empty batch instead of crashing
        # in torch.cat over an empty list.
        if not result:
            raise ValueError(
                "[InterleaveImageLists] Both image lists are empty; nothing to interleave."
            )
        return (torch.cat(result, dim=0),)

# NOTE: no NODE_CLASS_MAPPINGS here — ComfyUI only discovers the mapping in
# the package root __init__.py. A local mapping was present before and was
# silently dead code (a trap for future edits).
