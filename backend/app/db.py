import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


# Load backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is not set")

if not SUPABASE_SERVICE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_KEY is not set")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)