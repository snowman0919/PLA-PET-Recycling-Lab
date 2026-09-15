"""FreeCADCmd entry point; run with explicit main namespace."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().with_name('generate.py')),run_name='__main__')
