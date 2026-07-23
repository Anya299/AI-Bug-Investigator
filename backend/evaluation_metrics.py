import json


def normalize_text(text):
    return (
        text.lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace(".", "")
        .replace(",", "")
        .replace('"', "")
        .replace("'", "")
    )


def keyword_match(keyword, response_text):

    keyword = normalize_text(keyword)
    response_text = normalize_text(response_text)

    words = keyword.split()

    matched = 0

    for word in words:
        if word in response_text:
            matched += 1

    return matched >= max(1, len(words)-1)


def calculate_score(ai_response, expected_keywords):

    score = 0

    response_text = normalize_text(
        json.dumps(ai_response)
    )

    for keyword in expected_keywords:

        if keyword_match(keyword, response_text):
            score += 1

    return score


def evaluate_results():

    with open(
        "evaluation_results.json",
        "r",
        encoding="utf-8"
    ) as file:

        results = json.load(file)


    total_score = 0
    possible_score = 0


    print("\nDetailed Evaluation")
    print("===================")


    for result in results:

        if "ai_output" not in result:
            continue


        root_score = result.get(
            "root_score",
            0
        )

        fix_score = result.get(
            "fix_score",
            0
        )

        total = root_score + fix_score


        total_score += total
        possible_score += 6


        print(
            f"\nBug {result['id']}"
        )

        print(
            f"Root Score: {root_score}/3"
        )

        print(
            f"Fix Score: {fix_score}/3"
        )

        print(
            f"Total: {total}/6"
        )


    accuracy = round(
        (total_score / possible_score) * 100,
        2
    )


    print("\n===================")
    print("Final Evaluation")
    print("===================")

    print(
        f"Total Score: {total_score}/{possible_score}"
    )

    print(
        f"Accuracy: {accuracy}%"
    )


if __name__ == "__main__":

    evaluate_results()