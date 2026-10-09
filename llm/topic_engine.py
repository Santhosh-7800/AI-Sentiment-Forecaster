import re
from pathlib import Path

try:
    from keybert import KeyBERT
except ImportError:  # pragma: no cover - fallback for lightweight environments
    KeyBERT = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - fallback for lightweight environments
    SentenceTransformer = None

import pandas as pd

base = Path(__file__).resolve().parent.parent
file_path = base / "output" / "results.csv"

model = SentenceTransformer("all-MiniLM-L6-v2") if SentenceTransformer is not None else None
kw_model = KeyBERT(model) if KeyBERT is not None and model is not None else None


def extract_row_keywords(text):
    if not isinstance(text, str) or not text.strip():
        return ""

    if kw_model is None:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9']+", text.lower())
        stop_words = {"the", "and", "for", "with", "this", "that", "from", "into", "have", "has", "had", "were", "was", "is", "are", "on", "in", "of", "to", "a", "an", "it", "its", "as", "at", "be", "but", "not"}
        keywords = []
        for token in tokens:
            if len(token) > 2 and token not in stop_words:
                keywords.append(token)
        return ", ".join(list(dict.fromkeys(keywords))[:5])

    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=5,
    )

    return ", ".join([kw[0] for kw in keywords])


if __name__ == "__main__":
    df = pd.read_csv(file_path)
    df["row_keywords"] = df["clean_text"].apply(extract_row_keywords)
    df.to_csv(base / "output" / "row_keywords_results.csv", index=False)
