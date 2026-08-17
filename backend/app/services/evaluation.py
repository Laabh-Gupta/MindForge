from app.db import supabase
from google import genai
import os
import json


gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


EVALUATION_PROMPT = """
You are evaluating a user's performance in a Socratic debate training session.

Evaluate the user's performance based ONLY on the conversation provided.

Return ONLY valid JSON with this exact structure:

{
  "overall_score": 0,
  "summary": "short summary of the user's performance",
  "scores": [
    {
      "category": "critical_thinking",
      "score": 0,
      "strength": "one observed strength",
      "weakness": "one observed weakness",
      "evidence": "specific evidence from the conversation"
    },
    {
      "category": "argumentation",
      "score": 0,
      "strength": "one observed strength",
      "weakness": "one observed weakness",
      "evidence": "specific evidence from the conversation"
    },
    {
      "category": "clarity",
      "score": 0,
      "strength": "one observed strength",
      "weakness": "one observed weakness",
      "evidence": "specific evidence from the conversation"
    },
    {
      "category": "reasoning",
      "score": 0,
      "strength": "one observed strength",
      "weakness": "one observed weakness",
      "evidence": "specific evidence from the conversation"
    }
  ],
  "recommended_practice": []
}

Scores must be between 0 and 100.

Do not invent facts about the user.
Do not evaluate the AI's performance.
Evaluate only the user's reasoning, argumentation, clarity, critical thinking, and related skills.
"""


def evaluate_session(session_id: str, user_id: str):
    # 1. Load the completed session
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

    if not session:
        raise ValueError("Session not found.")

    # 2. Load the conversation
    messages = (
        supabase
        .table("messages")
        .select("role, content")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
        .data
    )

    if not messages:
        raise ValueError("No messages found for this session.")

    # 3. Build conversation text
    conversation = "\n\n".join(
        f"{message['role'].upper()}: {message['content']}"
        for message in messages
    )

    # 4. Ask Gemini to evaluate the session
    interaction = gemini_client.interactions.create(
        model="gemini-3.6-flash",
        input=(
            f"{EVALUATION_PROMPT}\n\n"
            f"Topic: {session['topic']}\n\n"
            f"Conversation:\n{conversation}"
        )
    )

    # 5. Parse Gemini's JSON response
    raw_output = interaction.output_text.strip()

    # Gemini may wrap valid JSON in Markdown code fences.
    if raw_output.startswith("```"):
        lines = raw_output.splitlines()

        # Remove opening ```json / ```
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        # Remove closing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        raw_output = "\n".join(lines).strip()

    try:
        evaluation = json.loads(raw_output)
    except json.JSONDecodeError:
        raise ValueError(
            f"Gemini returned invalid evaluation JSON: {raw_output}"
        )

    return evaluation