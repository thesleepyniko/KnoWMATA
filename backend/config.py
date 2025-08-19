from dotenv import load_dotenv
import os

load_dotenv()

class settings:
    WMATA_API_KEY: str = os.getenv("WMATA_API_KEY") or ""
    DATABASE_URL: str = os.getenv("DATABASE_URL") or ""