from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.db import supabase
from app.services.evaluation import evaluate_session
from app.services.personalization import (
    update_skill_scores,
    refresh_training_context,
)


router = APIRouter()


@router.post("/sessions/{session_id}/evaluate")
def evaluate_completed_session(
    session_id: str,
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

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    # 2. Only completed sessions can be evaluated
    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Session is not completed yet."
        )

    # 3. Run the evaluation engine
    try:
        evaluation = evaluate_session(
            session_id=session_id,
            user_id=user_id
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # 4. Save the overall evaluation
    evaluation_result = (
        supabase
        .table("session_evaluations")
        .insert({
            "session_id": session_id,
            "user_id": user_id,
            "overall_score": evaluation["overall_score"],
            "summary": evaluation["summary"],
            "recommended_practice": evaluation["recommended_practice"]
        })
        .execute()
    )

    if not evaluation_result.data:
        raise HTTPException(
            status_code=500,
            detail="Failed to save session evaluation."
        )

    saved_evaluation = evaluation_result.data[0]

    # 5. Save individual category scores
    score_rows = []

    for score in evaluation.get("scores", []):
        score_rows.append({
            "session_evaluation_id": saved_evaluation["id"],
            "category": score["category"],
            "score": score["score"],
            "strength": score["strength"],
            "weakness": score["weakness"],
            "evidence": score["evidence"]
        })

    if score_rows:
        try:
            (
                supabase
                .table("evaluation_scores")
                .insert(score_rows)
                .execute()
            )
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save evaluation scores: {error}"
            )

    # 6. Update the user's persistent skill profile
    try:
        update_skill_scores(
            user_id=user_id,
            evaluation_scores=score_rows
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update skill scores: {error}"
        )

    # 7. Rebuild the cached personalized training context
    try:
        refresh_training_context(user_id)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh training context: {error}"
        )

    # 8. Return the complete evaluation
    return {
        "evaluation": saved_evaluation,
        "scores": score_rows
    }