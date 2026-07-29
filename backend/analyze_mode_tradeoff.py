import json


data = json.load(open("evaluation_v2_results.json"))


tradeoffs = []


for item in data:

    if "quick" not in item or "full" not in item:
        continue

    quick = item["quick"]
    full = item["full"]

    if "total_score" in quick and "total_score" in full:

        difference = full["total_score"] - quick["total_score"]

        # meaningful difference
        if difference >= 1:
            tradeoffs.append({
                "id": item["id"],
                "bug": item["title"],
                "quick_score": quick["total_score"],
                "full_score": full["total_score"],
                "difference": difference,
                "tradeoff": "Full mode provides better investigation quality"
            })


result = {
    "analysis": "Quick vs Full mode quality tradeoff",
    "threshold": "Full mode score >= Quick mode score + 1",
    "cases": tradeoffs,
    "total_cases": len(tradeoffs)
}


with open("mode_tradeoff_analysis.json", "w") as f:
    json.dump(result, f, indent=4)


print("Mode tradeoff analysis completed")
print(f"Cases found: {len(tradeoffs)}")