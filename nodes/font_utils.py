import os
import glob

# Resolve the absolute path to the 'fonts' folder inside this custom node
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")

def get_available_fonts():
    """Returns a list of all .ttf and .otf files inside the bundled fonts/ directory."""
    if not os.path.exists(FONT_DIR):
        return ["default"]
        
    fonts = []
    for ext in ("*.ttf", "*.otf"):
        for path in glob.glob(os.path.join(FONT_DIR, ext)):
            fonts.append(os.path.basename(path))
            
    if not fonts:
        return ["default"]
        
    return sorted(fonts)

def get_font_path(font_filename):
    """Resolves a bundled font filename to an absolute path."""
    if font_filename == "default" or not font_filename:
        fonts = get_available_fonts()
        if fonts and fonts[0] != "default":
            font_filename = fonts[0]
        else:
            return "C:/Windows/Fonts/arial.ttf"
            
    # For backward compatibility with old saved workflows that have "C:/..."
    if "/" in font_filename or "\\" in font_filename:
        return font_filename
        
    return os.path.join(FONT_DIR, font_filename)
