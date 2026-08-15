# ComfyUI-Minibook Studio

## Overview
ComfyUI-Minibook Studio is a custom AI node and workflow automation suite designed for digital minibook production. It automates the sequential generation, formatting, and layout processing for complex multi-page or booklet assets, replacing fragmented manual assembly and repetitive prompting with a single-click execution pipeline.

## Project History & Evolution
The project was developed to solve the operational bottlenecks and stylistic drift associated with manual multi-page generation. The creator authored a proprietary "minibook" node suite containing custom backend nodes (Python) that handle procedural data passing, state management, and asset containment between generation blocks. 
The creator sought to feature this system in their Upwork portfolio to highlight their skills as an AI Workflow Architect and Custom Node Developer. During development, they explicitly guided the generation away from cliché themes, demanding "entertaining, yet absurd, but not entirely outlandish inputs... and for the love of god dont try to do any of this noir bullshit."

## Core Features / Architecture
- **ComfyUI Environment:** Runs on ComfyUI (v0.25.0) utilizing an NVIDIA GeForce RTX 3060 (12GB VRAM).
- **Custom Node Suite:** Modular backend logic written in Python to maintain strict stylistic and layout consistency across independent generation batches.
- **Multi-Stage Orchestration:** The workflow (`minibook_editorial_OptionA.json`) integrates LLM prompting (via OpenRouter API), image generation (SDXLClipModel, AutoencoderKL), and layout assembly.
- **AI Editor Pipeline:** Uses an LLM (such as `anthropic/claude-opus-4.7`) acting as a "senior literary editor and book designer." The LLM ingests a raw manuscript and produces a JSON-structured editorial plan detailing page numbers, page types (`text_only`, `full_illustration`, etc.), pacing notes, and illustration prompts.
- **PDF Export:** The final structured content is saved automatically to `output/minibook_editorial_output.pdf`.

## Prompts & Debugging
- **Upwork Portfolio Strategy:**
  > "I want to include my creation of the minibook node workflow and custom nodes in this upwork portfolio entry. can you suggest the best method of representing this visually on upwork as well as some ideas about the entries i have to present on this pasge"
- **Theme Generation:**
  > "ok i need entertaining, yet absurd, but not entirely outlandish inputs for the generation of another minibook asset. i'll need a theme, constraints, format, art direction, description of the main character. and for the love of god dont try to do any of this noir bullshit."
- **LLM Editorial Prompt:**
  > "Your job is to take a raw story manuscript and produce an EDITORIAL PLAN that breaks the story into pages intelligently. You are NOT just splitting by word count. You are making editorial decisions: Dramatic Pacing, Visual Rhythm, Breathing Room, Chapter Structure, Opening & Closing... Respond with ONLY valid JSON in this exact structure..."
- **Execution Logs:** Encountered and bypassed non-fatal warnings such as `insightface` (`FutureWarning: estimate is deprecated`) and ONNX (`UserWarning: Specified provider 'CUDAExecutionProvider' is not in available provider names`), successfully completing the 400+ second rendering jobs.

## Current State
The project is a fully functional, integrated multi-stage generation workflow within ComfyUI. The codebase is organized as a Git repository (`minibook-studio.git`). It successfully transforms raw manuscripts (like "CARTOGRAPHIES OF THE SMALL SELF" and "THE WEIGHT OF SALT") into finalized PDF booklets containing synchronized text and generated imagery.


---

> [!NOTE] Version / Alternative Note
> The following section comes from an alternative, earlier, or differently named document (`comfyui-minibook-node.md`) covering similar or overlapping ideas. There may be version differences.

# ComfyUI-MiniBook_Node & MiniBook Suite

## Overview
MiniBook Suite is a dual-LLM pipeline that turns a single prompt into a finished, illustrated, character-consistent storybook. It automates the roles of a Literary Editor, Art Director, and Layout Designer within the ComfyUI ecosystem.

## Project History & Evolution
- **Phase 1 (StorybookForge):** Initially attempted as a massive monolithic custom node, which proved too brittle and hard to debug.
- **Phase 2 (Hybrid Pipeline):** Pivoted to a modular architecture utilizing community nodes (`ComfyUI LLM Toolkit`, `ComfyUI_IPAdapter_plus`, `ComfyUI-Fill-Nodes`) alongside bespoke Python connective logic (`MiniBookFormatter` and `MiniBookArtDirectorPrompt`).
- **Phase 3 (Refinement):** Solved "orphan page" issues using a forward-merging algorithm to dynamically sweep up short pages.
- **Phase 4 (Noir LoRA):** Navigated 12GB VRAM limits on an RTX 3060 to train a cohesive "Noir" stylistic LoRA using OneTrainer with high Gradient Accumulation.
- **Phase 5 (V2 Context Formatting):** Upgraded the formatter to intelligently detect and paginate `storybook` prose, `poetry` stanzas, and `chaptered_story` formats without breaking structure.
- **Phase 6 (Deployment):** Replaced legacy code in the `ComfyUI-MiniBook_Node` repository and synced the V2 suite to GitHub.

## Architecture
The system utilizes a 4-phase architecture:
1. **The Author (LLM 1):** Generates the story text (GPT / Claude / GLM-4.2 via OpenRouter).
2. **The Typesetter (Custom Python):** `MiniBookFormatterV2` chunks text into pages using regex parsing, orphan-page merging, and dynamic illustration placement.
3. **The Art Director (LLM 2):** Writes tailored image prompts for each finished page to maintain coherent art direction.
4. **The Illustrator & Bindery:** SDXL + IPAdapter FaceID + Custom LoRA generates character-consistent art. Text is overlaid, and HTML/Images are converted to a final PDF.

## Current State
- The central GitHub repo is `FormAndNoise/ComfyUI-MiniBook_Node`.
- Working directory is synced via `H:\ComfyUI-MiniBook_Node`.
- Junction linked to `C:\Users\Aarik\ComfyUI-Installs\ComfyUI (2)\ComfyUI\custom_nodes\ComfyUI-MiniBook_Node`.
- Portfolio strategy relies on the narrative of precise engineering and systems integration, leveraging Aarik's background in ballet to highlight strict discipline and craftsmanship.


---

> [!NOTE] Version / Alternative Note
> The following section comes from an alternative, earlier, or differently named document (`comfyui-minibook-suite.md`) covering similar or overlapping ideas. There may be version differences.

# ComfyUI MiniBook Suite

## Overview
ComfyUI MiniBook Suite is a modular, dual-LLM pipeline that turns a single prompt into a finished, illustrated, and character-consistent storybook—automatically. Built as a suite of custom nodes for ComfyUI, the project acts as a Literary Editor, Art Director, and Layout Designer. It relies heavily on "AI-assisted development" and "LLM orchestration," utilizing models like GPT, Claude, and GLM-4.2 (via OpenRouter and Antigravity-CLI) to handle distinct tasks, while custom Python logic manages typesetting and pagination.

## Project History & Evolution
The project began as an overly ambitious monolithic custom node called **StorybookForge**. This approach proved brittle and impossible to debug; a failure anywhere killed the entire generation process. Realizing this, the user pivoted to a modular architecture, leveraging stable community nodes (like `ComfyUI-LLM-Toolkit` and `IPAdapter`) and building bespoke Python nodes only for missing connective logic.

The user, drawing from a 12-year professional career in the National Ballet of Canada, brought a deep understanding of rigorous structure and discipline to AI pipeline architecture. They realized they didn't need to hand-code everything; rather, they acted as a director—specifying logic, decomposing problems, and using AI to build and iterate the code. 

Key challenges overcome during evolution:
- **Orphan Pages:** Initial text chunking left pages with a single trailing word. A forward-merging algorithm was implemented to sweep up sub-threshold pages and combine them for clean, readable layouts.
- **Hardware Limitations:** Attempting batch generations on a consumer RTX 3060 (12GB VRAM) resulted in severe Out-of-Memory (OOM) crashes. The workflow was adapted to enforce strict one-at-a-time generation steps.
- **Dynamic Context Formatting:** An advanced `FormatterV2` was developed to intelligently detect and paginate based on input context (`storybook` prose vs. `poetry` stanzas vs. `chaptered_story`), ensuring structure was never broken across pages.

## Core Features / Architecture
The system utilizes a specialized, multi-stage pipeline:
1. **The Author (LLM 1):** Generates the underlying narrative from a prompt.
2. **The Typesetter (Custom Python):** Intelligently chunks text into pages via regex parsing, resolves orphan pages via forward-merging, and manages dynamic illustration placement.
3. **The Art Director (LLM 2):** Reads each paginated chunk and writes a tailored image prompt to maintain coherent art direction.
4. **The Illustrator (SDXL + IPAdapter FaceID):** Generates the illustrations while strictly enforcing character consistency across all pages.
5. **The Bindery:** Composites the text over the art and assembles the final product into a finished, printable PDF.

## Prompts & Debugging
Debugging required recognizing LLM behaviors and hardware constraints. For example, batch processing had to be dismantled due to 12GB VRAM limitations, trading speed for stability. Additionally, a critical regex loop bug that misnumbered chapters on empty string inputs was fixed via iterative testing with Claude.

The user discovered that by providing open-ended constraints, the LLM could intelligently infer and generate remarkable results.
**Key Prompt Setup for "Noir" Storybook:**
- **Theme:** "a burned-out detective piecing together one last case in a rain-soaked city that has already forgotten him"
- **Format:** "noir graphic novel"
- **Art Style (User Input):** "Line art illustration with gentle, broad sweeping ink washes"
- **Prompt Constraints:** "Dark and moody adult tone. Write in first-person with dry, cynical internal monologue. Include atmospheric details, moral ambiguity, and a plot that genuinely twists."
- **Character Description:** "Detective Jack Morrow: grizzled mid-40s man, unshaven with dark stubble, deep-set tired eyes, wearing a battered trench coat with the collar turned up, cigarette perpetually in the corner of his mouth, fedora casting half his face in shadow"

**LLM Art Director Interpretation:**
Instead of strictly following the user's art style, the LLM adapted it to fit the Noir theme: "high-contrast black and white ink illustration in the style of Frank Miller's Sin City, deep noir shadows, single amber-warm light source accent, rain-slicked streets, cinematic composition". This emergent behavior highlighted the power of leaving aesthetic execution open while strictly defining intent.

## Current State
- The final V2 suite is packaged and deployed to GitHub at `FormAndNoise/ComfyUI-MiniBook_Node`.
- It serves as the flagship portfolio project for the user, showcasing their ability to orchestrate complex AI workflows, design system architectures, and perform AI-assisted development.
- The pipeline reliably produces character-consistent, cleanly formatted PDF storybooks entirely within ComfyUI.


---

> [!NOTE] Version / Alternative Note
> The following section comes from an alternative, earlier, or differently named document (`comfyui-minibook.md`) covering similar or overlapping ideas. There may be version differences.

# ComfyUI-MiniBook

## Overview
A workflow design and pipeline for ComfyUI to create semi-customizable mini-books using existing native and custom nodes. It generates narrative text based on a user-provided theme, formats the text into pages, uses image generation for character-consistent illustrations, and outputs a formatted PDF mini-book.

## Project History & Evolution
- **Conceptual Pipeline:** The project started as a high-level step-by-step pipeline request (Narrative Generation, Text Formatting, Image Generation, Output and Constraints).
- **Pivot to ComfyUI:** The human user clarified that the entire workflow must be contained within a ComfyUI workflow, leading to a pivot using specific community nodes.
- **Custom Node Creation:** The user and AI regrouped to write custom Python nodes (`MiniBookFormatter`, `MiniBookArtDirectorPrompt`, `MiniBookPromptParser`, `InterleaveImageLists`) to fill missing logic gaps in text parsing and formatting.
- **Wiring Corrections:** Debugging JSON workflow structures revealed that user inputs (Theme Input String, Prompt Constraints) were disconnected from the MasterBookControl, which the AI then corrected.
- **LLM Integration Barrier:** The workflow hit a snag with the OpenRouter API returning a 404 error and connection closure when attempting to generate the story, halting execution at the LLM node.

## Core Features / Architecture
- **ComfyUI Node Packs:** Integrates `ComfyUI LLM Toolkit`, `ComfyUI_IPAdapter_plus`, `ComfyUI-Text-Processor`, `ComfyUI-Documents`, `ComfyUI-Book-Tools`, and `ComfyUI-Fill-Nodes`.
- **Phase 1: Narrative Generation:** Uses an LLM (via OpenRouter API) to generate a structured story based on a theme and format (storybook, short story, poem).
- **Phase 2: Text Formatting:** Employs `MiniBookFormatterV2` to split the text into discrete, page-sized outputs and assigns page roles.
- **Phase 3: Image Generation:** Ensures character consistency using `IPAdapter Unified Loader FaceID` paired with user-selected art styles and a generated visual prompt per page.
- **Phase 4: Book Assembly:** Uses `BTImageTextOverlay` to combine text and illustrations, and `FL_ImagesToPDF` to compile a complete PDF.

## Prompts & Debugging
- **Art Director Prompt:** 
  ```text
  You are the Art Director for a book. 
  The main character(s) look like this: {character_description}
  The global art style is: {art_style}
  Here is the story, broken down into pages:
  {numbered_pages_string}
  For EACH page, write a highly descriptive visual prompt for an AI image generator...
  ```
- **Debugging OpenRouter API Error:**
  - **Issue:** The LLM node failed during execution.
  - **Log:** `RuntimeError: [MiniBookFormatter] Story LLM returned an error instead of story text. Check your API key, model name, and OpenRouter account credits. Raw response: Error: Unexpected format: {'error': 'Connection closed'}`
  - **Log Details:** HTTP error 404 Not Found from OpenRouter API for the model `anthropic/claude-3.7-sonnet:thinking`.
  - **Resolution:** AI recommended validating the OpenRouter API key in the `.env` file and verifying if the specified Claude model name is correct and available.

## Current State
The pipeline is fully architected and constructed within ComfyUI, with custom nodes deployed and wired. However, execution is currently blocked by a network/API issue with OpenRouter returning a 404 error for the chosen LLM model.


---

> [!NOTE] Version / Alternative Note
> The following section comes from an alternative, earlier, or differently named document (`comfyui-storybook-forge.md`) covering similar or overlapping ideas. There may be version differences.

# ComfyUI-StorybookForge

## Overview
ComfyUI-StorybookForge is an automated book generation pipeline for ComfyUI. It is designed to take a basic story concept and turn it into a fully realized, multi-page storybook with minimal human intervention. The system uses a Language Model (LLM) to write and structure the story, generates corresponding illustrations with character continuity, renders styled text pages, and finally assembles and exports the pages formatted specifically for physical Coptic binding.

## Project History & Evolution
The project was initiated when the user requested a workflow distinct from latent space experiments. The user outlined an ambitious vision: a workflow that takes a story idea (e.g., storybook, short story, poem), uses an LLM to expand and format it into pages, designates specific pages for illustrations matching the text, enforces character continuity, and finally exports the sequence into a format prepared for a custom Coptic binding app.

The assistant architected a multi-stage pipeline utilizing custom Python nodes for ComfyUI. The solution seamlessly chains LLM text generation with diffusion model image generation. 

**Learning Curve & Regrouping:**
While building the pipeline, the assistant had to overcome the complexities of managing dynamic data lengths (variable number of story pages) within ComfyUI's statically linked node system. To solve this, the `STORY` type was implemented as a structured JSON dict passed directly between nodes. To ensure that illustrations generated in one batch didn't require complex loop nodes, the assistant utilized a `BatchPromptEncoder` to encode all illustration prompts simultaneously and feed them into a single batched `KSampler` step. Furthermore, the `BookExporter` node was engineered to calculate physical print dimensions and output a precise `book_metadata.json` mapping required for nesting and folding folios in Coptic binding.

## Core Features / Architecture
The project architecture involves a highly coordinated pipeline of custom nodes:
- **StoryGenerator:** Communicates with an LLM (OpenAI, Anthropic, or local Ollama) using a detailed system prompt to produce a structured JSON story containing page breaks, character profiles, and specific illustration prompts.
- **StoryParser:** Dissects the JSON, extracting character prompts, illustration prompts, and story text for downstream nodes.
- **BatchPromptEncoder:** Takes a list of illustration prompts and encodes them into a batched CONDITIONING output, allowing a single `KSampler` to generate all illustrations in one pass.
- **TextPageRenderer:** Renders the text sections of the story onto styled background images (incorporating fonts, word wrapping, and layout styles).
- **BookPageAssembler:** Interleaves the generated text pages and illustrations into the correct reading order.
- **BookExporter:** Exports the final ordered images as PNGs alongside a comprehensive `book_metadata.json`. It calculates the exact sheet mapping and blank padding pages required for printing and folding folios for Coptic binding.
- **UI Extensions:** Custom JavaScript provides themed node colors and console logging/status widgets for the LLM execution phases.

## Prompts & Debugging
- **Initial Prompt:** "new custom workflow. separate from all of this latent exploration. I need a workflow that takes an idea and turns itself into a fully realized project requiring minimal human editing... prompting a language model to write a story... an alottment of these pages would be reserved for illustrations... character identity must have continuity... sent through a small app that I wrote myself to appropriately place pages in the correct order for the pages to be folded and nested for coptic binding of the book."
- **Debugging & Iteration:** The assistant designed the `StoryGenerator` to output structured JSON via a hidden system prompt, ensuring the data could be reliably parsed by `StoryParser`. To address character continuity, the assistant suggested an optional enhancement utilizing `IPAdapter`, wherein character reference portraits are generated first and used to guide the primary `KSampler`.

## Current State
The project is fully realized as a complete ComfyUI node suite. It includes the backend Python logic, UI styling, and a complete JSON workflow that chains the `StoryGenerator`, samplers, text renderer, and exporter together. The pipeline successfully outputs a `StorybookForge` folder containing all pages, metadata, and instructions ready for the user's Coptic binding app.
