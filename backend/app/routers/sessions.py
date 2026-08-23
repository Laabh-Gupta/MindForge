from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone

from app.auth import get_current_user
from app.db import supabase
from app.services.personalization import get_training_context

# from google import genai
# import os

# router = APIRouter()
# gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

from groq import Groq
import os

router = APIRouter()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

GROQ_MODEL = "openai/gpt-oss-120b"

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

At the beginning of a new interview, before the candidate has given any answer,
you must start the conversation yourself. Briefly welcome the candidate and ask
them to introduce themselves, including their background and experience relevant
to the role. Do not wait for the candidate to initiate the conversation.

After the candidate has given their introduction, continue the interview naturally
based on what they actually say.

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

def get_candidate_context(session_id: str) -> str:
    docs = (
        supabase
        .table("documents")
        .select("type, content_text")
        .eq("session_id", session_id)
        .execute()
        .data
    )

    if not docs:
        return ""

    lines = ["CANDIDATE CONTEXT"]

    for doc in docs:
        if doc["type"] == "resume":
            lines.append(f"Resume:\n{doc['content_text']}")
        elif doc["type"] == "jd":
            lines.append(f"Job Description:\n{doc['content_text']}")

    lines.append(
        "\nUse specific details from the resume and/or job description above to ground "
        "your questions — reference actual experience, projects, or requirements rather "
        "than asking generically."
    )

    return "\n\n".join(lines)

class CreateSessionRequest(BaseModel):
    mode: str
    topic: str
    resume_text: str | None = None
    jd_text: str | None = None

class MessageRequest(BaseModel):
    content: str

@router.post("/sessions")
def create_session(
    req: CreateSessionRequest,
    user_id: str = Depends(get_current_user)
):
    result = supabase.table("sessions").insert({
        "user_id": user_id,
        "mode": req.mode,
        "topic": req.topic,
        "config": {},
        "status": "active"
    }).execute()

    session = result.data[0]

    if req.mode == "interview":
        docs = []

        if req.resume_text and req.resume_text.strip():
            docs.append({
                "user_id": user_id,
                "session_id": session["id"],
                "type": "resume",
                "content_text": req.resume_text.strip()
            })

        if req.jd_text and req.jd_text.strip():
            docs.append({
                "user_id": user_id,
                "session_id": session["id"],
                "type": "jd",
                "content_text": req.jd_text.strip()
            })

        if docs:
            supabase.table("documents").insert(docs).execute()

        # Generate the opening message.
        # This does NOT increment turn_count.
        training_context = get_training_context(user_id)
        candidate_context = get_candidate_context(session["id"])

        opening_instruction = (
            "\n\nThis is the very start of the interview. Begin by briefly welcoming "
            "the candidate and asking them to introduce themselves and their background "
            "relevant to this role. Do not ask any other question yet — just the opening "
            "welcome and introduction request."
        )

        full_prompt = f"{INTERVIEW_SYSTEM_PROMPT}{opening_instruction}"

        if training_context:
            full_prompt = f"{training_context}\n\n{full_prompt}"

        if candidate_context:
            full_prompt = f"{full_prompt}\n\n{candidate_context}"

        opening_response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"{full_prompt}\n\n"
                        f"Topic: {req.topic}"
                    )
                }
            ],
            temperature=0.7,
        )

        opening_message = opening_response.choices[0].message.content

        # Save opening message as AI message.
        # No user message is created.
        supabase.table("messages").insert({
            "session_id": session["id"],
            "role": "ai",
            "content": opening_message
        }).execute()

        # Return it to the frontend so it can display immediately.
        session["opening_message"] = opening_message

    return session

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
    if session["mode"] == "interview":
        candidate_context = get_candidate_context(session_id)

        if candidate_context:
            full_prompt = f"{full_prompt}\n\n{candidate_context}"

    # 5. Save user's message
    supabase.table("messages").insert({
        "session_id": session_id,
        "role": "user",
        "content": req.content
    }).execute()

    # 6. Build conversation history for Groq
    history = (
        supabase
        .table("messages")
        .select("role, content")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
        .data
    )

    groq_messages = [
        {
            "role": "system",
            "content": (
                f"{full_prompt}\n\n"
                f"Topic: {session['topic']}"
            )
        }
    ]

    for message in history:
        groq_role = "assistant" if message["role"] == "ai" else "user"

        groq_messages.append({
            "role": groq_role,
            "content": message["content"]
        })

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=groq_messages,
        temperature=0.7,
    )

    ai_reply = response.choices[0].message.content

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
            **session["config"]
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

@router.get("/sessions/history")
def get_session_history(
    user_id: str = Depends(get_current_user)
):
    result = (
        supabase
        .table("sessions")
        .select(
            "id, mode, topic, status, created_at, "
            "session_evaluations(overall_score)"
        )
        .eq("user_id", user_id)
        .eq("status", "completed")
        .order("created_at", desc=True)
        .execute()
    )

    return result.data