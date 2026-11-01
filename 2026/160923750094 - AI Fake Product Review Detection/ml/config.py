# All folder paths in one place. Works from any terminal folder.
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
MODEL_DIR = os.path.join(ROOT, "models")
DATA_FILE = os.path.join(DATA_DIR, "fake reviews dataset.csv")
