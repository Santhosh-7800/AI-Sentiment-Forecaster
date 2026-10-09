import pandas as pd
from pathlib import Path

base = Path(__file__).resolve().parent.parent
file_path = base / "output" / "row_keywords_results.csv"
file_path_news=base/"output"/"news_results.csv"
news_df = pd.read_csv(file_path_news)
reviews_df = pd.read_csv(file_path)
def calculate_sentiment(df):

    total = len(df)

    positive = len(df[df["sentiment_label"] == "Positive"])
    neutral = len(df[df["sentiment_label"] == "Neutral"])
    negative = len(df[df["sentiment_label"] == "Negative"])

    return {
        "positive": round((positive/total)*100,2) if total else 0,
        "neutral": round((neutral/total)*100,2) if total else 0,
        "negative": round((negative/total)*100,2) if total else 0
    }
def generate_report(query, sentiment, keywords):

    positive = sentiment["positive"]
    neutral = sentiment["neutral"]
    negative = sentiment["negative"]

    if keywords:
        top_features = ", ".join(keywords[:3])
    else:
        top_features = "product quality and performance"

    report = f"""
    {query.title()} shows strong discussion around {top_features}.
    Approximately {positive}% of customer feedback is positive,
    while {neutral}% is neutral and {negative}% negative.
    Users frequently highlight these aspects when evaluating the product.
    """

    return report
def analyze_product(query):

    words = query.lower().split()

    news_filtered = news_df[
        news_df["title"].str.lower().apply(
            lambda x: any(word in x for word in words) if isinstance(x, str) else False
        )
    ]

    reviews_filtered = reviews_df[
        reviews_df["clean_text"].str.lower().apply(
            lambda x: any(word in x for word in words) if isinstance(x, str) else False
        )
    ]

    combined = pd.concat([news_filtered, reviews_filtered])

    sentiment = calculate_sentiment(combined)

    keywords = []

    if not reviews_filtered.empty:
        keywords = (
            reviews_filtered["row_keywords"]
            .astype(str)
            .str.split(",")
            .explode()
            .str.strip()
            .value_counts()
            .head(5)
            .index.tolist()
        )

    report = generate_report(query, sentiment, keywords)

    return {
        "sentiment": sentiment,
        "keywords": keywords,
        "report": report
    }
