from app.db import supabase
from datetime import datetime, timezone

def build_training_context(user_id: str) -> str:
    """Reads skill_scores, formats the USER PROFILE / ADAPTATION RULES block."""
    scores = supabase.table("skill_scores").select("*").eq("user_id", user_id).execute().data

    if not scores:
        return ""  # new user, no history yet — no personalization block

    sorted_by_score = sorted(scores, key=lambda s: s["rolling_average"] or 0)
    weak = sorted_by_score[:3]
    strong = sorted_by_score[-3:]
    improving = [s for s in scores if s["trend"] == "improving"]
    stagnant = [s for s in scores if s["trend"] == "stagnant"]

    lines = ["USER PROFILE"]
    lines.append(f"- Strong areas: {', '.join(s['skill_name'] for s in strong)}")
    lines.append(f"- Weak areas: {', '.join(s['skill_name'] for s in weak)}")
    if improving:
        lines.append(f"- Improving: {', '.join(s['skill_name'] for s in improving)}")
    if stagnant:
        lines.append(f"- Persistent weaknesses: {', '.join(s['skill_name'] for s in stagnant)}")

    focus = weak[0]["skill_name"] if weak else None
    if focus:
        lines.append(f"\nTRAINING OBJECTIVE\nPush the user on {focus} this session, without making it feel like a test.")

    lines.append("\nADAPTATION RULES")
    lines.append("- Challenge weak areas more directly than strong ones.")
    lines.append("- Do not ease up on strong areas — raise the bar there instead.")
    lines.append("- Do not mention scores or skill names directly to the user; adapt behavior, don't narrate it.")

    return "\n".join(lines)


def refresh_training_context(user_id: str):
    """Call this right after an evaluation completes and skill_scores is updated."""
    context_text = build_training_context(user_id)
    session_count = supabase.table("skill_scores").select("sessions_count").eq("user_id", user_id).execute().data
    total_sessions = max((s["sessions_count"] for s in session_count), default=0)

    supabase.table("training_context").upsert({
        "user_id": user_id,
        "context_text": context_text,
        "based_on_sessions": total_sessions,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).execute()


def get_training_context(user_id: str) -> str:
    """Return cached training context for a user.
    New users without a training_context row get an empty context.
    """

    result = (
        supabase
        .table("training_context")
        .select("context_text")
        .eq("user_id", user_id)
        .execute()
    )

    if not result or not result.data:
        return ""

    return result.data[0]["context_text"]

def update_skill_scores(user_id: str, evaluation_scores: list[dict]):
    """
    Update the user's persistent skill profile from a completed evaluation.

    Each evaluation score should contain:
        {
            "category": "Critical Thinking",
            "score": 75
        }

    The user's skill profile is maintained across sessions.
    """

    for item in evaluation_scores:
        skill_name = item.get("category")
        new_score = item.get("score")

        if not skill_name or new_score is None:
            continue

        # Normalize score
        new_score = float(new_score)

        # Keep scores within the expected 0-100 range
        new_score = max(0, min(100, new_score))

        # Check whether this skill already exists
        existing = (
            supabase
            .table("skill_scores")
            .select("*")
            .eq("user_id", user_id)
            .eq("skill_name", skill_name)
            .execute()
        )

        if existing.data:
            previous = existing.data[0]

            previous_score = float(
                previous.get("current_score") or new_score
            )

            previous_average = float(
                previous.get("rolling_average") or previous_score
            )

            previous_sessions = int(
                previous.get("sessions_count") or 0
            )

            # New rolling average
            new_sessions = previous_sessions + 1

            new_average = (
                previous_average * previous_sessions + new_score
            ) / new_sessions

            # Determine trend
            difference = new_score - previous_average

            if difference >= 5:
                trend = "improving"
            elif difference <= -5:
                trend = "declining"
            else:
                trend = "stagnant"

            (
                supabase
                .table("skill_scores")
                .update({
                    "current_score": new_score,
                    "rolling_average": round(new_average, 2),
                    "sessions_count": new_sessions,
                    "trend": trend,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
                .eq("user_id", user_id)
                .eq("skill_name", skill_name)
                .execute()
            )

        else:
            # First time this skill has been evaluated
            (
                supabase
                .table("skill_scores")
                .insert({
                    "user_id": user_id,
                    "skill_name": skill_name,
                    "current_score": new_score,
                    "rolling_average": new_score,
                    "sessions_count": 1,
                    "trend": "stagnant",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
                .execute()
            )

    # Rebuild the cached instructor context
    refresh_training_context(user_id)