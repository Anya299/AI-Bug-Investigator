import json


RESULT_FILE = "evaluation_results.json"


def calculate_metrics():
    try:
        with open(RESULT_FILE, "r") as file:
            results = json.load(file)

    except FileNotFoundError:
        print("❌ evaluation_results.json not found")
        return

    total_cases = len(results)

    if total_cases == 0:
        print("❌ No evaluation data found")
        return

    scored_results = [r for r in results if r.get("score_percent") is not None]
    failed_results = [r for r in results if r.get("score_percent") is None]

    if not scored_results:
        print("❌ No test cases produced a scored response — every call failed before scoring.")
        print(f"   {len(failed_results)}/{total_cases} failed. Check 'error'/'status_code' fields in {RESULT_FILE}.")
        return

    total_score = sum(r["score_percent"] for r in scored_results)
    passed_cases = sum(1 for r in scored_results if r["score_percent"] >= 50)

    average_score = total_score / len(scored_results)
    accuracy = (passed_cases / len(scored_results)) * 100

    print("\n========== AI Bug Investigator Evaluation ==========")

    print(f"Total Test Cases: {total_cases}")
    print(f"Scored Cases: {len(scored_results)}")
    if failed_results:
        print(f"Failed (unscored) Cases: {len(failed_results)}  <-- excluded from accuracy/average below")
    print(f"Passed Cases (score >= 50): {passed_cases}")

    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Average Score: {average_score:.2f}/100")

    print("\nModel:")
    print("meta-llama/llama-3.1-8b-instruct")

    print("\nPrompt Version:")
    print("2.6.0")

    print("\n====================================================")


if __name__ == "__main__":
    calculate_metrics()