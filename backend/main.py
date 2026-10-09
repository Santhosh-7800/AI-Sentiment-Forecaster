import pandas as pd
import time 
from scraper.selenium_scraper import scrape_reviews,get_product_links
from scraper.news_scraper import scrape_news
from llm.sentiment_engine import get_sentiment
from utils.cleaner import clean_text

def run_pipeline():
    categories = {
        "electronics": "https://www.amazon.in/s?i=electronics",
        "clothes": "https://www.amazon.in/s?i=fashion",
        "essentials": "https://www.amazon.in/s?i=grocery"
    }
    all_results = []

    for category_name, category_url in categories.items():

        print(f"Scraping category: {category_name}")

        # Step 1: Get product links from category
        product_links = get_product_links(category_url)

        # Limit to avoid blocking
        product_links = product_links[:3]

        for product_url in product_links:

            print(f"Scraping product: {product_url}")

            try:
                raw_reviews = scrape_reviews(product_url)

                for item in raw_reviews:

                    cleaned = clean_text(item["text"])
                    sentiment = get_sentiment(cleaned)

                    all_results.append({
                        "category": category_name,
                        "platform": item["platform"],
                        "product_url": product_url,
                        "original_text": item["text"],
                        "clean_text": cleaned,
                        "sentiment_label": sentiment["label"],
                        "sentiment_score": sentiment["score"]
                    })

                time.sleep(5)

            except Exception as e:
                print(f"Error scraping {product_url}: {e}")
                continue

    df = pd.DataFrame(all_results)
    df.to_csv("output/results.csv", index=False)

    print("Saved category sentiment results to CSV.")

   
def run_news_pipeline():

    news_data = scrape_news()

    results = []

    for article in news_data:

        combined_text = article["title"] + " " + article["description"]
        cleaned = clean_text(combined_text)

        sentiment = get_sentiment(cleaned)

        results.append({
            "platform": "news",
            "keyword": article["keyword"],
            "title": article["title"],
            "description": article["description"],
            "sentiment_label": sentiment["label"],
            "sentiment_score": sentiment["score"],
            "published_date": article["published_date"]
        })

    df = pd.DataFrame(results)
    df.to_csv("output/news_results.csv", index=False)

    print("News sentiment analysis saved to CSV.")

if __name__ == "__main__":
    run_pipeline()
    print("Starting AI Sentiment Pipeline...")
    run_news_pipeline()
