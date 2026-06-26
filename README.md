# ComfyUI-MiniBook_Node

ComfyUI-MiniBook is a custom node extension and workflow designed to automate the creation of illustrated storybooks. It utilizes a dual-LLM pipeline to generate a narrative, split it into pages, act as an Art Director to design scene prompts, generate images via SDXL + IPAdapter, and package the final result into a PDF.

## Installation

1. Navigate to your ComfyUI `custom_nodes` directory:
   ```bash
   cd ComfyUI/custom_nodes
   ```

2. Clone this repository or extract the packaged zip file here:
   ```bash
   git clone https://github.com/your-username/ComfyUI-MiniBook_Node.git
   ```
   *(If you downloaded the `.zip`, simply extract the `ComfyUI-MiniBook_Node` folder into `custom_nodes/`)*

3. Restart ComfyUI.

## Dependencies

This node suite acts as the orchestration layer but requires several other excellent community custom nodes to run the included `minibook_workflow.json`:

- **[ComfyUI-LLM-Toolkit](https://github.com/M1kep/ComfyUI-LLM-Toolkit)**: Required for LLM text generation (`LLMToolkitTextGenerator`, `APIProviderSelectorNode`).
  *Note: Be sure to set up your `.env` file with `OPENROUTER_API_KEY` (or other provider) as per the toolkit's instructions and increase the `max_tokens` default if you expect stories larger than 1024 tokens.*
- **[ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus)**: Required for character consistency (`IPAdapterUnifiedLoaderFaceID`, `IPAdapterFaceID`).
- **[ComfyUI-Documents](https://github.com/M1kep/ComfyUI-Documents)**: Required for the final PDF compilation (`FL_ImagesToPDF`, `FL_PDFSaver`).
- **[ComfyUI-Book-Tools] / Text Overlay nodes**: Required for placing text onto images (`BTImageTextOverlay`).

*No additional `pip` dependencies are required beyond what standard ComfyUI and the above extensions use.*

## Usage

1. Load the `workflows/minibook_workflow.json` in ComfyUI.
2. Provide your overarching story theme, constraints, and character description in the `MasterBookControl` (or connected `TextInput` nodes).
3. Ensure your API Provider (e.g. OpenRouter) is configured in your `.env`.
4. Run the workflow. It will:
   - Generate the story.
   - Format the story into chunks/pages.
   - Generate prompt instructions for the Art Director.
   - The Art Director LLM creates a specific image prompt for each page.
   - The workflow runs KSampler iteratively to generate illustrations.
   - The text is overlaid, and everything is saved to `output/minibook_output.pdf`.

---

