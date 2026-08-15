# __init__.py

try:
    from .nodes.dual_llm_nodes import MiniBookFormatter, MiniBookFormatterV2, MiniBookArtDirectorPrompt, MiniBookPromptParser
    from .nodes.editorial_art_director import MiniBookEditorialArtDirector, MiniBookAssembler
    from .nodes.front_matter import MiniBookFrontMatter
    from .nodes.interleave import InterleaveImageLists
    from .nodes.layout_compositor import MiniBookLayoutCompositor
    from .nodes.literary_editor import MiniBookLiteraryEditor
    from .nodes.text_to_image import BookToolsTextToImage
    from .nodes.core_controls import (
        MiniBookTextParser,
        PromptConstructor,
        PromptConstructorV2,
        MasterBookControl,
        TextInput,
        BookToolsPromptSelector,
        BookToolsPromptSchedule,
        BookToolsLoop,
        BookToolsLoopStart,
        BookToolsLoopEnd,
        BookToolsEndQueue,
        BookToolsDownloadFont,
        BookToolsImageTextOverlay,
        BookToolsCalculateTextGrowth,
        BookToolsRandomTextOverlay,
    )
except ImportError:
    from nodes.dual_llm_nodes import MiniBookFormatter, MiniBookFormatterV2, MiniBookArtDirectorPrompt, MiniBookPromptParser
    from nodes.editorial_art_director import MiniBookEditorialArtDirector, MiniBookAssembler
    from nodes.front_matter import MiniBookFrontMatter
    from nodes.interleave import InterleaveImageLists
    from nodes.layout_compositor import MiniBookLayoutCompositor
    from nodes.literary_editor import MiniBookLiteraryEditor
    from nodes.text_to_image import BookToolsTextToImage
    from nodes.core_controls import (
        MiniBookTextParser,
        PromptConstructor,
        PromptConstructorV2,
        MasterBookControl,
        TextInput,
        BookToolsPromptSelector,
        BookToolsPromptSchedule,
        BookToolsLoop,
        BookToolsLoopStart,
        BookToolsLoopEnd,
        BookToolsEndQueue,
        BookToolsDownloadFont,
        BookToolsImageTextOverlay,
        BookToolsCalculateTextGrowth,
        BookToolsRandomTextOverlay,
    )

try:
    try:
        from .nodes.specialty_generators import (
            MiniBookEarlyReaderGenerator,
            MiniBookBilingualGenerator,
            MiniBookWorkbookGenerator,
            MiniBookCYOAGenerator,
        )
        from .nodes.madlibs import MiniBookMadLibsEngine
        from .nodes.pdf_helpers import (
            MiniBookImageListToBatch,
            MiniBookImagesToPDF,
            MiniBookPDFSaver,
        )
    except ImportError:
        from nodes.specialty_generators import (
            MiniBookEarlyReaderGenerator,
            MiniBookBilingualGenerator,
            MiniBookWorkbookGenerator,
            MiniBookCYOAGenerator,
        )
        from nodes.madlibs import MiniBookMadLibsEngine
        from nodes.pdf_helpers import (
            MiniBookImageListToBatch,
            MiniBookImagesToPDF,
            MiniBookPDFSaver,
        )
    _SPECIALTY_NODES_AVAILABLE = True
except Exception:
    _SPECIALTY_NODES_AVAILABLE = False

# Map the internal class names to the identifiers ComfyUI uses under the hood.
# NOTE: BookTools* and TextInput keep their original BT*/MiniBookTextInput IDs
# so pre-existing workflow JSON files continue to load without edits.
NODE_CLASS_MAPPINGS = {
    "MiniBookFormatter": MiniBookFormatter,
    "MiniBookFormatterV2": MiniBookFormatterV2,
    "MiniBookArtDirectorPrompt": MiniBookArtDirectorPrompt,
    "MiniBookPromptParser": MiniBookPromptParser,
    "MiniBookEditorialArtDirector": MiniBookEditorialArtDirector,
    "MiniBookAssembler": MiniBookAssembler,
    "MiniBookFrontMatter": MiniBookFrontMatter,
    "InterleaveImageLists": InterleaveImageLists,
    "MiniBookLayoutCompositor": MiniBookLayoutCompositor,
    "MiniBookLiteraryEditor": MiniBookLiteraryEditor,
    "BookToolsTextToImage": BookToolsTextToImage,

    # Core Controls
    "MiniBookTextParser": MiniBookTextParser,
    "PromptConstructor": PromptConstructor,
    "PromptConstructorV2": PromptConstructorV2,
    "MasterBookControl": MasterBookControl,
    "MiniBookTextInput": TextInput,

    # BookTools suite (original registration IDs)
    "BTPromptSelector": BookToolsPromptSelector,
    "BTPromptSchedule": BookToolsPromptSchedule,
    "BTLoop": BookToolsLoop,
    "BTLoopStart": BookToolsLoopStart,
    "BTLoopEnd": BookToolsLoopEnd,
    "BTEndQueue": BookToolsEndQueue,
    "BTImageTextOverlay": BookToolsImageTextOverlay,
    "BTDownloadFont": BookToolsDownloadFont,
    "BTTextGrowth": BookToolsCalculateTextGrowth,
    "BTRandomTextOverlay": BookToolsRandomTextOverlay,
    "BTTextToImage": BookToolsTextToImage,
}

# Map the internal identifiers to the clean, human-readable names shown in the UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniBookFormatter": "MiniBook Formatter (Legacy)",
    "MiniBookFormatterV2": "MiniBook Formatter V2",
    "MiniBookArtDirectorPrompt": "MiniBook Art Director Prompt",
    "MiniBookPromptParser": "MiniBook Prompt Parser",
    "MiniBookEditorialArtDirector": "Editorial Art Director",
    "MiniBookAssembler": "Book Assembler",
    "MiniBookFrontMatter": "Front Matter Generator",
    "InterleaveImageLists": "Interleave Image Lists",
    "MiniBookLayoutCompositor": "Layout Compositor",
    "MiniBookLiteraryEditor": "Literary Editor",
    "BookToolsTextToImage": "Text to Image (Book Tools)",

    # Core Controls
    "MiniBookTextParser": "Text Parser",
    "PromptConstructor": "Prompt Constructor",
    "PromptConstructorV2": "Prompt Constructor V2",
    "MasterBookControl": "[MiniBook] Master Book Control",
    "MiniBookTextInput": "[MiniBook] Text Input",

    # BookTools suite
    "BTPromptSelector": "[Book Tools] Prompt Selector",
    "BTPromptSchedule": "[Book Tools] Prompt Batch Schedule",
    "BTLoop": "[Book Tools] Loop",
    "BTLoopStart": "[Book Tools] Loop Start",
    "BTLoopEnd": "[Book Tools] Loop End",
    "BTEndQueue": "[Book Tools] End Queue",
    "BTImageTextOverlay": "[Book Tools] Image Text Overlay",
    "BTDownloadFont": "[Book Tools] Download Font",
    "BTTextGrowth": "[Book Tools] Calculate Text Growth",
    "BTRandomTextOverlay": "[Book Tools] Random Text Overlay",
    "BTTextToImage": "[Book Tools] Text to Image",
}

if _SPECIALTY_NODES_AVAILABLE:
    NODE_CLASS_MAPPINGS.update({
        "MiniBookMadLibsEngine": MiniBookMadLibsEngine,
        "MiniBookEarlyReaderGenerator": MiniBookEarlyReaderGenerator,
        "MiniBookBilingualGenerator": MiniBookBilingualGenerator,
        "MiniBookWorkbookGenerator": MiniBookWorkbookGenerator,
        "MiniBookCYOAGenerator": MiniBookCYOAGenerator,
        "MiniBookImageListToBatch": MiniBookImageListToBatch,
        "MiniBookImagesToPDF": MiniBookImagesToPDF,
        "MiniBookPDFSaver": MiniBookPDFSaver,
    })
    NODE_DISPLAY_NAME_MAPPINGS.update({
        "MiniBookMadLibsEngine": "MadLibs Story Engine",
        "MiniBookEarlyReaderGenerator": "Early Reader Generator",
        "MiniBookBilingualGenerator": "Bilingual Book Generator",
        "MiniBookWorkbookGenerator": "Workbook Generator",
        "MiniBookCYOAGenerator": "CYOA Book Generator",
        "MiniBookImageListToBatch": "List to Batch (MiniBook)",
        "MiniBookImagesToPDF": "PDF Compiler (MiniBook)",
        "MiniBookPDFSaver": "PDF Saver (MiniBook)",
    })

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
