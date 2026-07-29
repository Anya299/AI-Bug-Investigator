import json
from statistics import mean, median


def load(filename):
    with open(filename, "r") as f:
        return json.load(f)


def collect(results):
    root = []
    fix = []
    total = []
    latency = []

    for bug in results:
        for mode in ("quick", "full"):
            if mode not in bug:
                continue

            data = bug[mode]

            if "root_score" not in data:
                continue

            root.append(data["root_score"])
            fix.append(data["fix_score"])
            total.append(data["total_score"])
            latency.append(data["latency_ms"])

    return {
        "root_mean": round(mean(root), 2),
        "root_median": round(median(root), 2),
        "fix_mean": round(mean(fix), 2),
        "fix_median": round(median(fix), 2),
        "total_mean": round(mean(total), 2),
        "total_median": round(median(total), 2),
        "latency_mean": round(mean(latency), 2),
        "latency_median": round(median(latency), 2),
    }


v1 = collect(load("evaluation_v1_results.json"))
v2 = collect(load("evaluation_v2_results.json"))

print("\nAggregate Statistics\n")

for key in v1:
    print(f"{key:18}  V1: {v1[key]:6}   V2: {v2[key]:6}   Δ: {round(v2[key]-v1[key],2):6}")