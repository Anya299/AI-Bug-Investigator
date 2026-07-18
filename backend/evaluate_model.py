import json
import requests


API_URL = "http://127.0.0.1:8000/analyze-bug"


def load_dataset():
    with open("evaluation_dataset.json", "r") as file:
        return json.load(file)


def calculate_score(ai_response, expected_keywords):
    score = 0

    response_text = json.dumps(ai_response).lower()

    for keyword in expected_keywords:
        if keyword.lower() in response_text:
            score += 1

    return score


def run_evaluation():

    dataset = load_dataset()

    results = []

    for bug in dataset:

        print(f"Testing Bug {bug['id']}: {bug['title']}")

        payload = {
            "description": bug["bug_input"],
            "stack_trace": "",
            "language": "Unknown",
            "severity": "high"
        }

        response = requests.post(
            API_URL,
            json=payload
        )

        if response.status_code == 200:

            ai_result = response.json()

            root_score = calculate_score(
                ai_result,
                bug["expected_root_causes"]
            )

            fix_score = calculate_score(
                ai_result,
                bug["expected_fix"]
            )

            total_score = root_score + fix_score

            results.append({
                "id": bug["id"],
                "title": bug["title"],
                "root_score": root_score,
                "fix_score": fix_score,
                "total_score": total_score,
                "ai_output": ai_result
            })

        else:

            results.append({
                "id": bug["id"],
                "title": bug["title"],
                "error": response.text
            })


    with open(
        "evaluation_results.json",
        "w"
    ) as file:

        json.dump(
            results,
            file,
            indent=4
        )


    print("\nEvaluation Completed ✅")
    print("Results saved: evaluation_results.json")


if __name__ == "__main__":
    run_evaluation()