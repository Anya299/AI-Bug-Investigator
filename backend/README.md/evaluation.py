import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import anthropic

from config import get_settings
from logger import get_logger
from main import BugReportRequest, analyze_bug
from prompt import PROMPT_VERSION

logger = get_logger(__name__)
settings = get_settings()

RESULTS_DIR = Path("eval_results")

JUDGE_SYSTEM_PROMPT = """You are grading the output of a bug-investigation AI. \
Score the analysis on a 1-5 scale for each dimension below and respond ONLY \
with a JSON object with these exact keys (no other text):

- "specificity": 1-5, does it reference concrete technical details from the \
bug report rather than generic advice?
- "actionability": 1-5, could an engineer follow investigation_steps and \
fix_recommendation directly, without further clarification?
- "root_cause_plausibility": 1-5, is the root cause a reasonable, well-\
supported hypothesis given the bug description?
- "overall": 1-5, overall quality of the analysis.
- "notes": one sentence explaining the overall score."""


@dataclass
class GoldenCase:
    id: str
    description: str
    language: str | None = None
    severity: str | None = None
    stack_trace: str | None = None


GOLDEN_CASES: list[GoldenCase] = [
    GoldenCase(
        id="null_pointer_java",
        description=(
            "Users report the checkout page crashes with a 500 error only when "
            "they apply a discount code, but only for guest (non-logged-in) users. "
            "Logged-in users can apply discount codes fine."
        ),
        language="Java/Spring Boot", severity="high",
        stack_trace="java.lang.NullPointerException at CartService.applyDiscount(CartService.java:142)",
    ),
    GoldenCase(
        id="race_condition_python",
        description=(
            "Occasionally (roughly 1 in 500 requests) two concurrent requests to "
            "increment a user's credit balance result in one increment being lost. "
            "Balance is stored in Postgres and updated via a read-then-write in Python."
        ),
        language="Python/FastAPI", severity="critical",
    ),
    GoldenCase(
        id="css_layout_shift",
        description=(
            "On mobile Safari only, the product image on the product detail page "
            "loads and then the whole page jumps down by about 80px a second later."
        ),
        language="React", severity="low",
    ),
    GoldenCase(
        id="memory_leak_node",
        description=(
            "A Node.js worker process handling image resizing steadily grows in "
            "memory usage over 24 hours until it OOMs and gets restarted by the "
            "orchestrator. Restarting resets it, but it climbs again."
        ),
        language="Node.js", severity="high",
    ),
    GoldenCase(id="vague_short_report", description="The app is slow sometimes.", severity="medium"),
]


def check_structure(result) -> list[str]:
    """Fast, free, no-LLM structural sanity checks."""
    problems = []
    if len(result.bug_summary.strip()) < 10:
        problems.append("bug_summary too short")
    if len(result.root_cause.strip()) < 10:
        problems.append("root_cause too short")
    if len(result.investigation_steps) < 2:
        problems.append("investigation_steps has fewer than 2 steps")
    if any(len(step.strip()) < 5 for step in result.investigation_steps):
        problems.append("investigation_steps contains a near-empty step")
    if len(result.fix_recommendation.strip()) < 10:
        problems.append("fix_recommendation too short")
    if len(result.prevention.strip()) < 10:
        problems.append("prevention too short")
    return problems


async def judge_result(case: GoldenCase, result) -> dict:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=settings.request_timeout_seconds)
    payload = {"bug_report": asdict(case), "analysis": result.model_dump()}
    response = await client.messages.create(
        model=settings.anthropic_model, max_tokens=400,
        system=JUDGE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(payload, indent=2)}],
    )
    raw = "\n".join(b.text for b in response.content if b.type == "text").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Judge returned non-JSON for case %s: %s", case.id, raw[:200])
        return {"overall": None, "notes": "judge parsing failed"}


async def run_case(case: GoldenCase) -> dict:
    request = BugReportRequest(
        description=case.description, language=case.language,
        severity=case.severity, stack_trace=case.stack_trace,
    )
    start = time.perf_counter()
    error = None
    result = None
    try:
        result = await analyze_bug(request)
    except Exception as exc:
        error = str(exc)
    elapsed = round(time.perf_counter() - start, 2)

    if error:
        return {"id": case.id, "status": "error", "error": error, "latency_s": elapsed}

    structural_problems = check_structure(result)
    judge_scores = await judge_result(case, result)

    return {
        "id": case.id,
        "status": "ok" if not structural_problems else "structural_issues",
        "latency_s": elapsed,
        "structural_problems": structural_problems,
        "judge_scores": judge_scores,
        "output": result.model_dump(),
    }


async def run_evaluation() -> dict:
    logger.info("Running evaluation on %d golden cases (prompt_v=%s)", len(GOLDEN_CASES), PROMPT_VERSION)
    results = await asyncio.gather(*(run_case(case) for case in GOLDEN_CASES))

    ok_count = sum(1 for r in results if r["status"] == "ok")
    overall_scores = [r["judge_scores"]["overall"] for r in results if r.get("judge_scores", {}).get("overall") is not None]
    avg_score = round(sum(overall_scores) / len(overall_scores), 2) if overall_scores else None

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION,
        "model": settings.anthropic_model,
        "total_cases": len(GOLDEN_CASES),
        "passed_structural": ok_count,
        "avg_judge_score": avg_score,
        "results": results,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(report, indent=2))

    print(f"\n{'='*60}\nEvaluation complete — prompt v{PROMPT_VERSION} / {settings.anthropic_model}\n{'='*60}")
    print(f"Structural pass:  {ok_count}/{len(GOLDEN_CASES)}")
    print(f"Avg judge score:  {avg_score}/5" if avg_score else "Avg judge score:  N/A")
    for r in results:
        marker = "✅" if r["status"] == "ok" else "⚠️ " if r["status"] == "structural_issues" else "❌"
        score = r.get("judge_scores", {}).get("overall", "-")
        print(f"  {marker} {r['id']:<24} latency={r.get('latency_s', '-'):>5}s  judge={score}")
    print(f"\nFull report: {out_path}\n{'='*60}\n")
    return report


if __name__ == "__main__":
    asyncio.run(run_evaluation())