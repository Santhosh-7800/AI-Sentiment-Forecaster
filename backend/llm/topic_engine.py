# from bertopic import BERTopic
# from sentence_transformers import SentenceTransformer
# from bertopic.representation import KeyBERTInspired
# from sklearn.feature_extraction.text import CountVectorizer
# import pandas as pd
# from pathlib import Path

# base = Path(__file__).resolve().parent.parent
# file_path = base / "output" / "results.csv"

# df = pd.read_csv(file_path)

# df = df[df["clean_text"].notna()]
# df = df[df["clean_text"].str.strip() != ""]

# docs = df["clean_text"].tolist()

# embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
# custom_stopwords = [
#     "good","nice","product","using","really","very",
#     "got","buy","bought","use"
# ]
# vectorizer_model = CountVectorizer(
#     stop_words="english",
#     ngram_range=(1,2),
#     min_df=2
# )
# vectorizer_model.stop_words_ = set(custom_stopwords)
# representation_model = KeyBERTInspired()
# topic_model = BERTopic(
#     embedding_model=embedding_model,
#     vectorizer_model=vectorizer_model,
#     representation_model=representation_model,
#     min_topic_size=5
# )

# topics, probs = topic_model.fit_transform(docs)

# df["topic"] = topics

# print(topic_model.get_topic_info())

# for topic in topic_model.get_topics():
#     if topic == -1:
#         continue
#     print(f"\nTopic {topic}")
#     print(topic_model.get_topic(topic))

# topic_sentiment = df.groupby(["topic","sentiment_label"]).size().unstack()

# topic_sentiment_pct = topic_sentiment.div(topic_sentiment.sum(axis=1), axis=0) * 100

# print("\nTopic Sentiment %:")
# print(topic_sentiment_pct)

# topic_keywords = {}

# for topic in topic_model.get_topics():
#     if topic == -1:
#         continue
#     words = topic_model.get_topic(topic)
#     if words:
#         keywords = ", ".join([w[0] for w in words[:5]])
#         topic_keywords[topic] = keywords

# df["topic_keywords"] = df["topic"].map(topic_keywords)

# df.to_csv(base / "output" / "topics_results.csv", index=False)

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

# Load embedding model only when those libraries are available.
model = SentenceTransformer("all-MiniLM-L6-v2") if SentenceTransformer is not None else None
kw_model = KeyBERT(model) if KeyBERT is not None and model is not None else None

# keywords_list = []

# for text in df["clean_text"]:
    
#     if not text.strip():
#         keywords_list.append("")
#         continue

#     keywords = kw_model.extract_keywords(
#         text,
#         keyphrase_ngram_range=(1,2),
#         stop_words="english",
#         top_n=5
#     )

#     words = [kw[0] for kw in keywords]
#     keywords_list.append(", ".join(words))

# df["row_keywords"] = keywords_list
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
        keyphrase_ngram_range=(1,2),
        stop_words="english",
        top_n=5
    )

    return ", ".join([kw[0] for kw in keywords])


if __name__ == "__main__":
    df = pd.read_csv(file_path)
    df["row_keywords"] = df["clean_text"].apply(extract_row_keywords)
    df.to_csv(base / "output" / "row_keywords_results.csv", index=False)
