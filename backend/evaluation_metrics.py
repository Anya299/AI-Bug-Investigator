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


    total_score = 0
    passed_cases = 0


    for item in results:

        # Supports different key names
        score = (
            item.get("score")
            or item.get("accuracy")
            or item.get("evaluation_score")
            or 0
        )

        total_score += score

        if score >= 50:
            passed_cases += 1


    average_score = total_score / total_cases
    accuracy = (passed_cases / total_cases) * 100


    print("\n========== AI Bug Investigator Evaluation ==========")

    print(f"Total Test Cases: {total_cases}")
    print(f"Passed Cases: {passed_cases}")

    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Average Score: {average_score:.2f}/100")

    print("\nModel:")
    print("meta-llama/llama-3.1-8b-instruct")

    print("\nPrompt Version:")
    print("2.5.1")

    print("\n====================================================")


if __name__ == "__main__":
    calculate_metrics()