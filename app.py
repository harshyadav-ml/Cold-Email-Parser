"""Root proxy for Streamlit application (Phase 5).

Run with:
    streamlit run app.py
    or:
    streamlit run streamlit_app.py
"""
import runpy
from pathlib import Path

_TARGET = Path(__file__).parent / "streamlit_app.py"
runpy.run_path(str(_TARGET), run_name="__main__")
