"""
Hugging Face Spaces entry point.
Re-exports the FastAPI app from backend.main
"""
import os
import sys

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
