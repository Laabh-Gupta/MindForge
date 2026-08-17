from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone

from app.auth import get_current_user
from app.db import supabase
from app.services.personalization import get_training_context

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

INTERVIEW_SYSTEM_PROMPT = """You are conducting a professional interview. Your job is to
genuinely assess the candidate's thinking, not run through a script.

For every candidate answer:
1. Understand what they actually said — their reasoning, not just the topic.
2. Identify anything vague, inconsistent, or under-explained.
3. Ask exactly ONE natural follow-up question that either:
   - digs deeper into their specific answer, or
   - challenges an inconsistency you noticed, or
   - asks them to clarify something vague.

Never ask a random unrelated question from a generic bank. Every question must connect
to what the candidate just said. Stay professional and direct — like a real interviewer,
not overly friendly or overly harsh.

Do not evaluate or score the candidate out loud during the interview — that happens
separately, afterward."""


def get_system_prompt(mode: str) -> str:
    if mode == "interview":
        return INTERVIEW_SYSTEM_PROMPT
    return DEBATE_SYSTEM_PROMPT

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
def send_message(
    session_id: str,
    req: MessageRequest,
    user_id: str = Depends(get_current_user)
):
    # 1. Load the session belonging to the authenticated user
    session = (
        supabase
        .table("sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .single()
        .execute()
        .data
    )

    # 2. Stop if the session has already concluded
    if session["concluded_at"] is not None:
        return {
            "error": "Session has already concluded.",
            "concluded": True
        }

    # 3. Stop if the maximum number of turns has already been reached
    if session["turn_count"] >= session["max_turns"]:
        supabase.table("sessions").update({
            "status": "completed",
            "concluded_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", session_id).execute()

        return {
            "error": "Maximum number of turns reached.",
            "concluded": True
        }

    # 4. Get personalized training context
    training_context = get_training_context(user_id)

    mode_prompt = get_system_prompt(session["mode"])

    full_prompt = (
        f"{training_context}\n\n{mode_prompt}"
        if training_context
        else mode_prompt
    )

    # 5. Save user's message
    supabase.table("messages").insert({
        "session_id": session_id,
        "role": "user",
        "content": req.content
    }).execute()

    # 6. Continue Gemini conversation if one exists
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
            input=(
                f"{full_prompt}\n\n"
                f"Topic: {session['topic']}\n\n"
                f"User: {req.content}"
            )
        )

    ai_reply = interaction.output_text

    # 7. Save AI reply
    supabase.table("messages").insert({
        "session_id": session_id,
        "role": "ai",
        "content": ai_reply
    }).execute()

    # 8. Increment turn count
    new_turn_count = session["turn_count"] + 1

    # 9. Conclude session if maximum turns reached
    concluded = new_turn_count >= session["max_turns"]

    update_data = {
        "turn_count": new_turn_count,
        "config": {
            **session["config"],
            "last_interaction_id": interaction.id
        }
    }

    if concluded:
        update_data["status"] = "completed"
        update_data["concluded_at"] = datetime.now(timezone.utc).isoformat()

    # 10. Update session
    supabase.table("sessions").update(
        update_data
    ).eq("id", session_id).execute()

    return {
        "reply": ai_reply,
        "turn_count": new_turn_count,
        "max_turns": session["max_turns"],
        "concluded": concluded
    }