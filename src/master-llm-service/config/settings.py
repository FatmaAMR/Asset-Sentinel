import os
from dotenv import load_dotenv
from pathlib import Path

# Setup paths
CURRENT_FILE = Path(__file__).resolve()
# Locating the root directory 'Asset-Sentinel'
ROOT_DIR = next(p for p in CURRENT_FILE.parents if p.name == "Asset-Sentinel")
load_dotenv(dotenv_path=ROOT_DIR / ".env")

class Settings:
   pass

settings = Settings()




