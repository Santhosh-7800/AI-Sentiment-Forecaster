try:
    from transformers import pipeline
except ImportError:  # pragma: no cover - fallback for lightweight environments
    pipeline = None

if pipeline is not None:
    sentiment_model = pipeline(
        "text-classification",
        model="cardiffnlp/twitter-roberta-base-sentiment",
        truncation=True,
    )
else:
    sentiment_model = None


def get_sentiment(text):
    if sentiment_model is None:
        import re
        tokens = re.findall(r"[a-zA-Z']+", str(text or "").lower())
        positive = {"good", "great", "excellent", "love", "amazing", "positive", "superb", "best"}
        negative = {"bad", "terrible", "awful", "hate", "poor", "worst", "broken", "waste"}
        pos_hits = sum(1 for token in tokens if token in positive)
        neg_hits = sum(1 for token in tokens if token in negative)
        score = pos_hits - neg_hits
        label = "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"
        return {"label": label, "score": float(max(-1.0, min(1.0, score / max(1, len(tokens)))))}

    result = sentiment_model(text[:512])[0]

    label_map = {
        "LABEL_0": "Negative",
        "LABEL_1": "Neutral",
        "LABEL_2": "Positive"
    }

    return {
        "label": label_map[result["label"]],
        "score": float(result["score"])
    }
