from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import get_current_user
from app.db import supabase
from google import genai
import os

router = APIRouter()
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

DEBATE_SYSTEM_PROMPT = """You are a Socratic debate coach. Your job is NOT to simply
argue with the user or agree with them.

For every user message, respond using EXACTLY this format, with these exact three
labels, every time, no variations:

**Claim:** [restate their claim in one sentence]
**Assumption:** [name the key assumption they're making]
**Question:** [ask exactly ONE question that challenges that assumption]

If the user asks "what do you mean?" or asks for clarification, use the same three
labels, but make the Question section a rephrasing of your previous point instead of
a new question — explain it differently, do not repeat it verbatim.

Never inject unrelated facts, statistics, or generic filler. Stay strictly on the
user's actual topic. Never add extra sections beyond these three."""

class CreateSessionRequest(BaseModel):
    mode: str
    topic: str

class MessageRequest(BaseModel):
    content: str

@router.post("/sessions")
def create_session(req: CreateSessionRequest, user_id: str = Depends(get_current_user)):
    result = supabase.table("sessions").insert({
        "user_id": user_id,
        "mode": req.mode,
        "topic": req.topic,
        "config": {},
        "status": "active"
    }).execute()
    return result.data[0]

@router.post("/sessions/{session_id}/messages")
def send_message(session_id: str, req: MessageRequest, user_id: str = Depends(get_current_user)):
    # 1. Load session (RLS + explicit user_id check both apply)
    session = supabase.table("sessions").select("*").eq("id", session_id).eq("user_id", user_id).single().execute().data

    # 2. Save the user's message
    supabase.table("messages").insert({
        "session_id": session_id, "role": "user", "content": req.content
    }).execute()

    # 3. Call Gemini — continue the thread if one exists, else start fresh with the system prompt
    prev_id = session["config"].get("last_interaction_id")
    if prev_id:
        interaction = gemini_client.interactions.create(
            model="gemini-3.6-flash",
            input=req.content,
            previous_interaction_id=prev_id
        )
    else:
        interaction = gemini_client.interactions.create(
            model="gemini-3.6-flash",
            input=f"{DEBATE_SYSTEM_PROMPT}\n\nTopic: {session['topic']}\n\nUser: {req.content}"
        )

    ai_reply = interaction.output_text

    # 4. Save the AI's reply
    supabase.table("messages").insert({
        "session_id": session_id, "role": "ai", "content": ai_reply
    }).execute()

    # 5. Remember the interaction thread for next turn
    supabase.table("sessions").update({
        "config": {**session["config"], "last_interaction_id": interaction.id}
    }).eq("id", session_id).execute()

    return {"reply": ai_reply}