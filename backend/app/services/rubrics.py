DEBATE_CATEGORIES = [
    "critical_thinking",
    "argumentation",
    "clarity",
    "reasoning"
]


INTERVIEW_CATEGORIES = [
    "communication",
    "structure",
    "critical_thinking",
    "confidence",
    "relevance",
    "consistency",
    "domain_awareness",
]


RUBRICS = {
    "debate": DEBATE_CATEGORIES,
    "interview": INTERVIEW_CATEGORIES,
}


MODE_LABELS = {
    "debate": "a Socratic debate training session",
    "interview": "a professional interview simulation",
}


def get_categories(mode: str) -> list[str]:
    return RUBRICS.get(mode, DEBATE_CATEGORIES)


def get_mode_label(mode: str) -> str:
    return MODE_LABELS.get(
        mode,
        "a communication training session"
    )