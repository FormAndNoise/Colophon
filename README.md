# Colophon: An LLM-Driven Publishing Suite for ComfyUI

![Colophon Workflow](assets/screen.png)

Colophon is a modular suite of ComfyUI custom nodes designed to automate the roles of a Literary Editor, Art Director, and Layout Designer. Rather than blindly chunking text or generating disconnected images, this pipeline uses LLM orchestration to build cohesive, formatted, and visually consistent storybooks and graphic novels.

## 📖 The Concept: Human-in-the-Loop Orchestration
Built for the demands of modern creative studios, MiniBook operates on the philosophy of the **Human-in-the-Loop Director**. This is not an automated content mill. It is a highly controlled pipeline that empowers a human creator to curate, audit, and refine the AI's output. 

By separating the logic into distinct editorial and layout steps, you retain absolute creative control over dramatic pacing, visual consistency, and typographic elegance. The outputs are generated sequentially, perfectly nested, and ready for digital publishing or physical print imposition.

## 🚀 Key Features
* **Intelligent Pagination:** The `Literary Editor` node paginates raw text based on dramatic beats, chapter breaks, and visual rhythm, rather than arbitrary word counts.
* **Latent Space Locking:** The `Editorial Art Director` node programmatically binds global art styles and character embeddings to local scene prompts, ensuring absolute visual consistency across the entire book.
* **Dynamic Layout Engine:** The `Layout Compositor` handles real typography, drop caps, margins, and text-to-image integration, rendering complete pages rather than raw assets.
* **API-Agnostic Routing:** Seamlessly route LLM calls to cloud providers (OpenRouter, CLōD) for rapid prototyping, or to local endpoints for completely sovereign, air-gapped generation.

## 💻 Hardware & Compute Tiers
This suite is designed to be accessible for prototyping while scaling gracefully for enterprise production.

* **Prototyping & Development:** Validated and heavily tested on a standard NVIDIA RTX 3060 (12GB VRAM) paired with an Intel i5 / 24GB RAM secondary machine. By leveraging OpenRouter/CLōD for the heavy editorial logic, the entire layout and diffusion pipeline runs smoothly on mid-tier hardware.
* **Production & Sovereign Studios:** For studios requiring strict data privacy and IP protection, the API bridge can be pointed to a local network appliance running high-weight models on multi-GPU setups.

## 🧩 Core Node Breakdown
* **Literary Editor:** An LLM-powered editorial brain that reads a manuscript and outputs a strict JSON pagination plan.
* **Editorial Art Director:** Intercepts the editorial plan, extracting illustration notes and merging them with global stylistic anchors.
* **Layout Compositor:** Turns text arrays and image batches into properly formatted book pages with real typography.
* **Front Matter Generator:** Adds professional polish—title pages, copyright colophons, dedications, and back-cover blurbs.
* **Master Book Control:** The central hub for defining global themes, formats, art styles, and character descriptions.

### 🧰 Core Controls & Utility Nodes
Included in this suite are several robust utility nodes for advanced workflow control:
* **Image Text Overlay:** Add highly customizable, format-aware text overlays directly to image tensors.
* **Prompt Selection & Scheduling:** Manage and format string prompts based on configurable parameters, input indices, and pre/post-text application.
* **Loop Constructs (`Loop`, `LoopStart`, `LoopEnd`):** Implement dynamic looping mechanisms that reset based on runtime conditions.
* **EndQueue:** Conditional logic to terminate the current generation queue.

## 🛠️ Installation & Requirements

### System Requirements
* Python 3.6+
* `Pillow` (PIL) for image processing
* `torch` for tensor operations
* `numpy`

### Installation
1. Navigate to your ComfyUI `custom_nodes` directory.
2. Clone this repository:
   ```bash
   git clone [https://github.com/yourusername/minibook-studio.git](https://github.com/yourusername/minibook-studio.git)
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Restart ComfyUI.

### Required Community Nodes
To run the included example workflows out-of-the-box, it is highly recommended to use the **ComfyUI Manager** to install the following dependencies:
* `comfyui-llm-toolkit` (For API Provider configuration)
* `ComfyUI_IPAdapter_plus` (For character FaceID and latent consistency)

## 📥 Quick Start
Drop the provided `minibook_editorial_OptionA.json` from the `workflows/` directory into your ComfyUI workspace. Configure your API key in the LLM Provider node, input a short story into the Theme Input, and queue the prompt. 

*Sample spreads and final PDF outputs can be viewed in the `assets/` folder.*

## 🤝 Contributions
Contributions are welcome. Please fork the repository and submit a pull request with your suggested changes.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.