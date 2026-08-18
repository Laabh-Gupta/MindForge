from app.db import supabase
# from google import genai
import os
import json


# gemini_client = genai.Client(
#     api_key=os.getenv("GEMINI_API_KEY")
# )

from groq import Groq

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

GROQ_MODEL = "openai/gpt-oss-120b"


from app.services.rubrics import get_categories, get_mode_label


def build_evaluation_prompt(mode: str) -> str:
    categories = get_categories(mode)
    label = get_mode_label(mode)

    category_blocks = ",\n".join(
        f'''    {{
      "category": "{cat}",
      "score": 0,
      "strength": "one observed strength",
      "weakness": "one observed weakness",
      "evidence": "specific evidence from the conversation"
    }}'''
        for cat in categories
    )

    return f"""
You are evaluating a user's performance in {label}.

Evaluate the user's performance based ONLY on the conversation provided.

Return ONLY valid JSON with this exact structure:

{{
  "overall_score": 0,
  "summary": "short summary of the user's performance",
  "scores": [
{category_blocks}
  ],
  "recommended_practice": []
}}

Scores must be between 0 and 100.

Do not invent facts about the user.
Do not evaluate the AI's performance.
Evaluate only the user's demonstrated skills relevant to {label}.
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
    evaluation_prompt = build_evaluation_prompt(session["mode"])

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": evaluation_prompt
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {session['topic']}\n\n"
                    f"Conversation:\n{conversation}"
                )
            }
        ],
        temperature=0.2,
    )

    raw_output = response.choices[0].message.content.strip()

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
            f"Groq returned invalid evaluation JSON: {raw_output}"
        )

    return evaluation