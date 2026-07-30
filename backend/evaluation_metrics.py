import json


RESULT_FILE = "evaluation_results.json"


def _summarize(entries, label):
    """entries: list of per-mode result dicts (e.g. all the 'quick' dicts,
    or all the 'full' dicts) across every bug."""
    scored = [e for e in entries if e.get("score_percent") is not None]
    failed = [e for e in entries if e.get("score_percent") is None]

    print(f"\n--- {label} mode ---")
    print(f"Total: {len(entries)}  Scored: {len(scored)}  Failed: {len(failed)}")

    if not scored:
        print("No scored responses in this mode.")
        return

    total_score = sum(e["score_percent"] for e in scored)
    passed = sum(1 for e in scored if e["score_percent"] >= 50)
    avg_score = total_score / len(scored)
    accuracy = (passed / len(scored)) * 100
    avg_latency = sum(e.get("latency_ms", 0) for e in scored) / len(scored)

    print(f"Passed (>=50): {passed}/{len(scored)}")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Average Score: {avg_score:.2f}/100")
    print(f"Average Latency: {avg_latency:.0f} ms")


def calculate_metrics():
    try:
        with open(RESULT_FILE, "r") as file:
            results = json.load(file)
    except FileNotFoundError:
        print("❌ evaluation_results.json not found")
        return

    total_bugs = len(results)
    if total_bugs == 0:
        print("❌ No evaluation data found")
        return

    quick_entries = [r["quick"] for r in results if r.get("quick")]
    full_entries = [r["full"] for r in results if r.get("full")]

    print("\n========== AI Bug Investigator Evaluation ==========")
    print(f"Total Bugs Tested: {total_bugs}")

    _summarize(quick_entries, "Quick")
    _summarize(full_entries, "Full")

    print("\nModel:")
    print("meta-llama/llama-3.1-8b-instruct")

    print("\nPrompt Version:")
    print("2.6.0")

    print("\n====================================================")


if __name__ == "__main__":
    calculate_metrics()