import json
import requests
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# FREE, FAST, LOCAL grader using TF-IDF + cosine similarity.
# No API calls, no large model downloads (scikit-learn is a small install
# you likely already have). Runs in well under a second for 20 bugs.
#
# Trade-off vs. true embeddings: this matches based on shared words/roots,
# not deep meaning. So "release unused resources" vs "close unclosed
# connections" will get partial credit for overlapping words like
# "resources"/"unused", but won't catch pure synonyms with zero shared
# vocabulary as well as sentence-transformers would. Good enough to move
# fast today; you can swap in the embeddings version later if you want
# more accuracy and have time to let the model download in the background.
# ---------------------------------------------------------------------------

SIMILARITY_THRESHOLD = 0.15  # TF-IDF similarities run lower than embedding
                              # similarities since it's pure word overlap.
                              # Tune this after eyeballing a few results.

API_URL = "http://127.0.0.1:8000/analyze-bug"

# Paste your JWT access token here. It expires (access_token_expire_minutes
# in config.py) -- if every bug in a run comes back 401, this is stale,
# get a fresh one from /auth/login before re-running.
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiaG9vbWlAdGVzdC5jb20iLCJleHAiOjE3ODUzOTI2NDd9.fJTAwxQFvIqwqInwnmLC_SU1yX7SPUaPUL73PSLGcYM"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}"
}


def load_dataset():
    with open("evaluation_dataset.json", "r") as file:
        return json.load(file)


def response_to_text(ai_response):
    parts = [
        ai_response.get("bug_summary", ""),
        ai_response.get("root_cause", ""),
        " ".join(ai_response.get("investigation_steps", []) or []),
        ai_response.get("fix_recommendation", ""),
        ai_response.get("prevention", ""),
    ]
    return " ".join(p for p in parts if p)


def calculate_score_tfidf(ai_response, expected_keywords):
    response_text = response_to_text(ai_response)

    chunks = [c.strip() for c in response_text.replace(";", ".").split(".") if c.strip()]
    if not chunks:
        chunks = [response_text]

    # Fit TF-IDF over (chunks + keywords) together so they share a vocabulary space
    corpus = chunks + expected_keywords
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Happens if corpus is all stopwords / empty after stripping
        return 0, [{"keyword": k, "matched": False, "similarity": 0.0, "best_matching_text": ""} for k in expected_keywords]

    chunk_vectors = tfidf_matrix[:len(chunks)]
    keyword_vectors = tfidf_matrix[len(chunks):]

    sims = cosine_similarity(keyword_vectors, chunk_vectors)  # [num_keywords, num_chunks]

    score = 0
    match_details = []
    for i, keyword in enumerate(expected_keywords):
        best_sim = float(sims[i].max())
        best_chunk_idx = int(sims[i].argmax())
        matched = best_sim >= SIMILARITY_THRESHOLD
        if matched:
            score += 1
        match_details.append({
            "keyword": keyword,
            "matched": matched,
            "similarity": round(best_sim, 3),
            "best_matching_text": chunks[best_chunk_idx]
        })

    return score, match_details


def run_evaluation():

    dataset = load_dataset()
    comparison_results = []

    total_possible = 0
    total_earned = 0
    failed_calls = 0

    for bug in dataset:

        print(f"Testing Bug {bug['id']}: {bug['title']}")

        bug_result = {
            "id": bug["id"],
            "title": bug["title"],
            "quick": {},
            "full": {}
        }

        payload = {
            "description": bug["bug_input"],
            "language": "Unknown",
            "severity": "high"
        }

        if bug.get("stack_trace"):
            payload["stack_trace"] = bug["stack_trace"]

        for mode in ["quick", "full"]:

            payload["mode"] = mode

            start_time = time.time()

            response = requests.post(
                API_URL,
                json=payload,
                headers=HEADERS
            )

            time.sleep(2)

            latency_ms = round(
                (time.time() - start_time) * 1000,
                2
            )

            if response.status_code == 200:

                ai_result = response.json()

                root_score, _ = calculate_score_tfidf(
                    ai_result,
                    bug["expected_root_causes"]
                )

                fix_score, _ = calculate_score_tfidf(
                    ai_result,
                    bug["expected_fix"]
                )

                bug_result[mode] = {
                    "root_score": root_score,
                    "fix_score": fix_score,
                    "total_score": root_score + fix_score,
                    "latency_ms": latency_ms
                }

                total_earned += root_score + fix_score

                total_possible += (
                    len(bug["expected_root_causes"])
                    +
                    len(bug["expected_fix"])
                )

                print(
                    f"{bug['title']} | {mode} | {latency_ms} ms"
                )

            else:
                failed_calls += 1

                bug_result[mode] = {
                    "error": response.text,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms
                }

                print(
                    f"Failed: {bug['title']} | {mode} | {response.status_code}"
                )

        comparison_results.append(bug_result)


    with open("evaluation_results.json", "w") as file:
        json.dump(comparison_results, file, indent=4)


    accuracy = (
        (total_earned / total_possible) * 100
        if total_possible > 0
        else 0
    )

    print("\nEvaluation Completed ✅")
    print("Results saved: evaluation_results.json")
    print(f"Total Score: {total_earned}/{total_possible}")
    print(f"Accuracy: {accuracy:.1f}%")

    if failed_calls:
        print(
            f"⚠ {failed_calls} API calls failed"
        )

    print(
        f"\n(Similarity threshold used: {SIMILARITY_THRESHOLD})"
    )


if __name__ == "__main__":
    run_evaluation()

