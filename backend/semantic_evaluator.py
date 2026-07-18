from sentence_transformers import SentenceTransformer, util


model = SentenceTransformer(
    "paraphrase-MiniLM-L3-v2"
)


def similarity_score(text1, text2):

    embeddings = model.encode(
        [text1, text2],
        convert_to_tensor=True
    )

    score = util.cos_sim(
        embeddings[0],
        embeddings[1]
    )

    return float(score)


def check_root_cause(ai_output, expected_keywords):

    best_score = 0

    for keyword in expected_keywords:

        score = similarity_score(
            ai_output,
            keyword
        )

        if score > best_score:
            best_score = score

    return round(best_score, 2)