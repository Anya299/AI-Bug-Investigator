def calculate_confidence(
    *,
    stack_trace: str | None = None,
    description: str | None = None,
    framework: str | None = None,
    environment: str | None = None,
    reproduction_steps: str | None = None,
    expected_behavior: str | None = None,
    actual_behavior: str | None = None,
    pattern_match: bool = False,
) -> int:

    score = 0

    # Error evidence
    if stack_trace:
        error_keywords = [
            "error",
            "exception",
            "traceback",
            "failed",
            "failure",
            "timeout",
            "refused"
        ]

        if any(k in stack_trace.lower() for k in error_keywords):
            score += 30

    # Description quality
    if description:
        words = description.split()

        if len(words) >= 5:
            score += 10

        if len(words) >= 15:
            score += 10

    # Reproduction information
    if reproduction_steps:
        score += 15

    # Expected vs actual behavior
    if expected_behavior and actual_behavior:
        score += 15

    # Environment context
    if framework or environment:
        score += 10

    # Known pattern
    if pattern_match:
        score += 10

    return min(score, 100)