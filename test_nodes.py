import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from nodes.specialty_generators import (
        MiniBookEarlyReaderGenerator,
        MiniBookBilingualGenerator,
        MiniBookWorkbookGenerator,
        MiniBookCYOAGenerator
    )
    from nodes.madlibs import MiniBookMadLibsEngine
    
    print("All classes imported successfully!")
    
    # Instantiate them to make sure no __init__ errors
    e = MiniBookEarlyReaderGenerator()
    b = MiniBookBilingualGenerator()
    w = MiniBookWorkbookGenerator()
    c = MiniBookCYOAGenerator()
    m = MiniBookMadLibsEngine()
    
    print("All classes instantiated successfully!")
    
except Exception as e:
    print(f"Error: {e}")
