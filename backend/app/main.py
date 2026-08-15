import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from supabase import create_client

from app.auth import get_current_user
from app.routers.sessions import router as sessions_router


# Load backend/.env explicitly
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


app = FastAPI()


# CORS — allow the Vite dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


# Gemini client
gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# Register routers
app.include_router(sessions_router)


@app.get("/health")
def health():
    result = supabase.table("sessions").select("id").limit(1).execute()

    return {
        "status": "ok",
        "db_reachable": True
    }


@app.get("/test-ai")
def test_ai():
    interaction = gemini_client.interactions.create(
        model="gemini-3.6-flash",
        input="Say hello in one sentence."
    )

    return {
        "reply": interaction.output_text
    }


@app.get("/whoami")
def whoami(user_id: str = Depends(get_current_user)):
    return {
        "user_id": user_id
    }