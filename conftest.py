import sys
import os

# Ensure the repo root is on sys.path so that `app` is importable when running
# pytest from the project root without installing the package.
sys.path.insert(0, os.path.dirname(__file__))
