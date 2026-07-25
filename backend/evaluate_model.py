import json
import requests

def calculate_score(ai_response, expected_keywords):

    response_text = normalize_text(
        json.dumps(ai_response)
    )

    score = 0


    synonym_map = {

        "memory leak": [
            "memory leak",
            "memory growth",
            "heap exhaustion",
            "continuous object creation"
        ],

        "unused resources": [
            "unused resources",
            "unclosed resources",
            "resource leak",
            "database connections",
            "file handles"
        ],

        "memory allocation issue": [
            "memory allocation",
            "object creation",
            "garbage collection"
        ],


        "concurrent access": [
            "concurrent access",
            "shared state",
            "multiple threads"
        ],

        "thread synchronization": [
            "thread synchronization",
            "mutex",
            "lock",
            "semaphore"
        ],

        "timing issue": [
            "timing issue",
            "race condition",
            "interleaving"
        ],


        "hidden characters": [
            "hidden characters",
            "unicode characters",
            "invisible characters"
        ],

        "formatting issue": [
            "formatting issue",
            "whitespace",
            "trailing whitespace"
        ],


        "layout calculation": [
            "layout calculation",
            "css box model",
            "layout"
        ],

        "container size": [
            "container size",
            "container boundaries"
        ],


        "compiler optimization": [
            "compiler optimization",
            "optimization flags"
        ],

        "debug configuration": [
            "debug configuration",
            "debugger settings"
        ],


        "dependency mismatch": [
            "dependency mismatch",
            "package conflict",
            "version conflict"
        ],


        "legacy code": [
            "legacy code",
            "old code",
            "outdated architecture"
        ],

        "technical debt": [
            "technical debt",
            "lack of documentation",
            "legacy system"
        ]
    }


    for keyword in expected_keywords:

        keyword = normalize_text(keyword)

        matched = False


        if keyword in response_text:
            matched = True


        for key, values in synonym_map.items():

            if keyword == key:

                for value in values:
                    if value in response_text:
                        matched = True
                        break


        if matched:
            score += 1


    return score

API_URL = "http://127.0.0.1:8000/analyze-bug"

# Paste your JWT access token here
TOKEN =  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiaG9vbWlAdGVzdC5jb20iLCJleHAiOjE3ODQ5NDc1NDd9.t77zp1u6Vsj1zFSsb2UUmdL0S8M_C2xDgQvcbynpavo"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}"
}


def load_dataset():
    with open("evaluation_dataset.json", "r") as file:
        return json.load(file)


def normalize_text(text):
    return (
        text.lower()
        .replace("-", " ")
        .replace("_", " ")
    )


def calculate_score(ai_response, expected_keywords):
    response_text = normalize_text(json.dumps(ai_response))
    score = 0

    synonym_map = {

    # Memory leak
    "memory leak": [
        "memory leak",
        "memory growth",
        "heap exhaustion",
        "increasing memory usage"
    ],

    "unused resources": [
        "unused resources",
        "resource leak",
        "unclosed resources",
        "unclosed database connections",
        "file handles",
        "connections not closed"
    ],

    "memory allocation issue": [
        "memory allocation",
        "heap allocation",
        "heap exhaustion",
        "memory usage growth"
    ],


    # Race condition
    "concurrent access": [
        "concurrent access",
        "shared mutable state",
        "multiple threads accessing"
    ],

    "thread synchronization": [
        "thread synchronization",
        "synchronization",
        "mutex",
        "lock",
        "semaphore"
    ],

    "timing issue": [
        "timing issue",
        "race condition",
        "interleaving"
    ],


    # Hidden characters
    "hidden characters": [
        "hidden characters",
        "invisible characters",
        "non printable"
    ],

    "formatting issue": [
        "formatting issue",
        "whitespace",
        "trailing whitespace"
    ],

    "invisible characters": [
        "invisible characters",
        "hidden characters",
        "whitespace"
    ],


    # CSS issues
    "layout calculation": [
        "layout calculation",
        "layout",
        "css property"
    ],

    "container size": [
        "container size",
        "dimensions",
        "container boundaries"
    ],

    "responsive design problem": [
        "responsive design",
        "responsive",
        "flexbox",
        "grid layout"
    ],


    # Debugger/compiler
    "compiler optimization": [
        "compiler optimization",
        "optimization",
        "compiler flags"
    ],

    "debug configuration": [
        "debug configuration",
        "debug build",
        "debugger settings"
    ],

    "build mismatch": [
        "build mismatch",
        "release build",
        "version mismatch"
    ],


    # Dependency conflicts
    "dependency mismatch": [
        "dependency mismatch",
        "dependency conflict",
        "package conflict"
    ],

    "incompatible versions": [
        "incompatible versions",
        "version conflict",
        "different versions"
    ],

    "library conflict": [
        "library conflict",
        "dependency conflict",
        "package conflict"
    ],


    # Legacy code
    "legacy code": [
        "legacy code",
        "old code",
        "legacy system"
    ],

    "technical debt": [
        "technical debt",
        "legacy system",
        "old architecture",
        "lack of documentation"
    ]
}

    for keyword in expected_keywords:
        keyword = normalize_text(keyword)
        variations = synonym_map.get(keyword, [keyword])

        for variation in variations:
            if variation in response_text:
                score += 1
                break

    return score


def run_evaluation():
    dataset = load_dataset()
    results = []

    total_possible = 0
    total_earned = 0

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
            json=payload,
            headers=HEADERS
        )

        print(response.status_code)
        print(response.text)

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
            possible_score = len(bug["expected_root_causes"]) + len(bug["expected_fix"])

            total_earned += total_score
            total_possible += possible_score

            results.append({
                "id": bug["id"],
                "title": bug["title"],
                "root_score": root_score,
                "fix_score": fix_score,
                "total_score": total_score,
                "possible_score": possible_score,
                "ai_output": ai_result
            })

        else:
            results.append({
                "id": bug["id"],
                "title": bug["title"],
                "error": response.text
            })

    with open("evaluation_results.json", "w") as file:
        json.dump(results, file, indent=4)

    accuracy = (total_earned / total_possible) * 100 if total_possible > 0 else 0

    print("\nEvaluation Completed ✅")
    print("Results saved: evaluation_results.json")
    print(f"Total Score: {total_earned}/{total_possible}")
    print(f"Accuracy: {accuracy:.1f}%")


if __name__ == "__main__":
    run_evaluation()