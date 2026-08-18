import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from google import genai
from groq import Groq
from supabase import create_client

from app.auth import get_current_user
from app.routers.sessions import router as sessions_router
from app.routers.evaluations import router as evaluations_router


# Load backend/.env explicitly
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# Create FastAPI application
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


# # Gemini client
# gemini_client = genai.Client(
#     api_key=os.getenv("GEMINI_API_KEY")
# )

# Groq Client

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

GROQ_MODEL = "openai/gpt-oss-120b"


# Register routers
app.include_router(sessions_router)
app.include_router(evaluations_router)


@app.get("/health")
def health():
    result = (
        supabase
        .table("sessions")
        .select("id")
        .limit(1)
        .execute()
    )

    return {
        "status": "ok",
        "db_reachable": True
    }


# @app.get("/test-ai")
# def test_ai():
#     interaction = gemini_client.interactions.create(
#         model="gemini-3.6-flash",
#         input="Say hello in one sentence."
#     )

#     return {
#         "reply": interaction.output_text
#     }

@app.get("/test-ai")
def test_ai():
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": "Say hello in one sentence."
            }
        ],
        temperature=0.2,
    )

    return {
        "reply": response.choices[0].message.content
    }


@app.get("/whoami")
def whoami(user_id: str = Depends(get_current_user)):
    return {
        "user_id": user_id
    }