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

    # Direct error evidence
    if stack_trace:
        error_keywords = [
            "error",
            "exception",
            "traceback",
            "failed",
            "failure",
            "timeout",
            "refused",
            "modulenotfounderror",
            "keyerror",
            "typeerror",
            "valueerror",
        ]

        if any(k in stack_trace.lower() for k in error_keywords):
            score += 40

    # Exact traceback lines
    if stack_trace and ("File \"" in stack_trace or "line " in stack_trace):
        score += 15

    # Good description
    if description:
        words = description.split()

        if len(words) >= 5:
            score += 10

        if len(words) >= 15:
            score += 10

    # Context
    if framework:
        score += 10

    if environment:
        score += 5

    # Reproduction
    if reproduction_steps:
        score += 10

    # Expected vs actual
    if expected_behavior and actual_behavior:
        score += 10

    # Verified pattern
    if pattern_match:
        score += 15


    return min(score, 100)