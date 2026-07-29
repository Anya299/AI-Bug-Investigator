import json


def load_file(filename):
    with open(filename, "r") as f:
        return json.load(f)


v1 = load_file("evaluation_v1_results.json")
v2 = load_file("evaluation_v2_results.json")


def calculate_accuracy(results):
    total_score = 0
    total_possible = 0

    for bug in results:
        for mode in ["quick", "full"]:
            if mode not in bug:
                continue

            data = bug[mode]

            if "total_score" not in data:
                continue

            total_score += data["total_score"]

            # Each bug has 3 expected root causes + 3 expected fixes = 6 points.
            # Two modes (quick + full) => 12 possible points per bug.
            total_possible += 6

    if total_possible == 0:
        return 0

    return round((total_score / total_possible) * 100, 2)


v1_accuracy = calculate_accuracy(v1)
v2_accuracy = calculate_accuracy(v2)

print("Prompt Comparison")
print("----------------------------")
print(f"Prompt V1 Accuracy : {v1_accuracy}%")
print(f"Prompt V2 Accuracy : {v2_accuracy}%")
print(f"Improvement        : {round(v2_accuracy - v1_accuracy, 2)}%")

comparison = {
    "prompt_v1_accuracy": v1_accuracy,
    "prompt_v2_accuracy": v2_accuracy,
    "improvement": round(v2_accuracy - v1_accuracy, 2),
}

with open("prompt_comparison.json", "w") as f:
    json.dump(comparison, f, indent=4)

print("\nSaved: prompt_comparison.json")