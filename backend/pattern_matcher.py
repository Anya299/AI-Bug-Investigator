"""
Matches an incoming bug report against verified BugPattern records.

This is what makes "quick fix" actually fast: a bug that matches a known,
previously-verified pattern can return instantly, with no LLM round trip.
It also feeds context into the LLM prompt on full-mode requests, so even
when we do call the model, it's grounded in patterns we've already seen
rather than starting from zero every time.
"""

from database import SessionLocal
from models import BugPattern


def _score_pattern(pattern: BugPattern, error_text: str, language: str | None, framework: str | None) -> float:
    """
    Higher score = more confident this pattern actually matches. Plain
    substring containment on error_type is the strongest single signal;
    tags, language, framework, and verification status add supporting
    evidence on top of that.
    """
    error_text_lower = (error_text or "").lower()
    score = 0.0

    if pattern.error_type and pattern.error_type.lower() in error_text_lower:
        score += 50

    if pattern.error_message and pattern.error_message.lower() in error_text_lower:
        score += 20

    if pattern.tags:
        tag_hits = sum(
            1
            for tag in pattern.tags.split(",")
            if tag.strip() and tag.strip().lower() in error_text_lower
        )
        score += min(tag_hits, 3) * 8

    if language and pattern.language and pattern.language.lower() == language.lower():
        score += 15

    if framework and pattern.framework and pattern.framework.lower() == framework.lower():
        score += 15

    if pattern.is_verified:
        score += 10

    score += min(max(pattern.success_rate or 0.0, 0.0), 1.0) * 10

    return score


def find_matching_pattern(
    error_text: str,
    language: str | None = None,
    framework: str | None = None,
    min_score: float = 50.0,
) -> BugPattern | None:
    """
    Returns the single best-matching BugPattern, or None if nothing clears
    min_score. Only the error_type substring hit alone (50) clears the
    default threshold on its own -- everything else is supporting signal,
    which keeps this from confidently matching on a weak tag hit alone.
    """
    if not error_text or not error_text.strip():
        return None

    db = SessionLocal()
    try:
        patterns = db.query(BugPattern).all()

        scored = [
            (pattern, _score_pattern(pattern, error_text, language, framework))
            for pattern in patterns
        ]
        scored = [(pattern, score) for pattern, score in scored if score >= min_score]

        if not scored:
            return None

        scored.sort(key=lambda pair: pair[1], reverse=True)
        best_pattern, _best_score = scored[0]
        return best_pattern
    finally:
        db.close()


def record_pattern_usage(pattern_id: int) -> None:
    """
    Bumps usage_count when a pattern is actually used to answer a request
    (either as an instant quick-mode answer or as LLM grounding context),
    so usage_count reflects real usage instead of sitting at 0 forever.
    """
    db = SessionLocal()
    try:
        pattern = db.get(BugPattern, pattern_id)
        if pattern:
            pattern.usage_count = (pattern.usage_count or 0) + 1
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()