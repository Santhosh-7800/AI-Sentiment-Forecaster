from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from oauth2 import verify_access_token
from routers import authentication
import sys
from pymongo import MongoClient
import pandas as pd
import time

from scraper.selenium_scraper import scrape_reviews, get_product_links
from scraper.news_scraper import scrape_news
from llm.sentiment_engine import get_sentiment
from utils.cleaner import clean_text
print("PYTHON PATH:", sys.executable)

app = FastAPI()

app.include_router(authentication.router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@app.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    return {"message": "You are authorized", "user": payload}


client = MongoClient("mongodb://localhost:27017")
db = client["ai_project_db"]
product_collection = db["product_results"]
news_collection = db["news_results"]

# -----------------------
# Product Scraping Route
# -----------------------

@app.get("/run-products")
def run_pipeline():

    categories = {
        "electronics": "https://www.amazon.in/s?i=electronics",
        "clothes": "https://www.amazon.in/s?i=fashion",
        "essentials": "https://www.amazon.in/s?i=grocery"
    }
   
    all_results = []

    for category_name, category_url in categories.items():

        product_links = get_product_links(category_url)
        product_links = product_links[:3]

        for product_url in product_links:

            try:
                raw_reviews = scrape_reviews(product_url)
                print("Reviews found:", len(raw_reviews))

                for item in raw_reviews:

                    cleaned = clean_text(item["text"])
                    sentiment = get_sentiment(cleaned)
                    print("Sentiment:", sentiment)

                    data = {
                      "category":category_name,
                      "product_url": product_url,
                      "review": item["text"],
                      "sentiment_label": sentiment["label"],
                      "confidence_score": sentiment["confidence_score"],
                      "negative_percent": sentiment["percentages"]["Negative"],
                      "neutral_percent": sentiment["percentages"]["Neutral"],
                      "positive_percent": sentiment["percentages"]["Positive"],
                    }

                    all_results.append(data)
                    product_collection.insert_one(data)
                    print("Inserted:", data)

                time.sleep(5)

            except Exception as e:
                print(f"Error scraping {product_url}: {e}")
                continue

    return {"message": "Product scraping completed", "count": len(all_results)}

# -----------------------
# News Scraping Route
# -----------------------

@app.get("/run-news")
def run_news_pipeline():

    news_data = scrape_news()
    results = []

    for article in news_data:

        combined_text = article["title"] + " " + article["description"]
        cleaned = clean_text(combined_text)
        sentiment = get_sentiment(cleaned)

        data = {
            "platform": "news",
            "keyword": article["keyword"],
            "title": article["title"],
            "description": article["description"],
            "sentiment_label": sentiment["label"],
            "sentiment_score": sentiment["confidence_score"],
            "published_date": article["published_date"]
        }

        results.append(data)
        news_collection.insert_one(data)

    return {"message": "News scraping completed", "count": len(results)}

# -----------------------
# Get Stored Products
# -----------------------

@app.get("/products")
def get_products():
    data = list(product_collection.find({}, {"_id": 0}))
    return data

# -----------------------
# Get Stored News
# -----------------------

@app.get("/news")
def get_news():
    data = list(news_collection.find({}, {"_id": 0}))
    return data

