import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def scrape_news(keywords=["amazon", "flipkart", "myntra"], max_articles=20):

    all_articles = []

    for keyword in keywords:

        url = f"https://news.google.com/rss/search?q={keyword}"

        response = requests.get(url)
        root = ET.fromstring(response.content)

        count = 0

        for item in root.findall(".//item"):

            if count >= max_articles:
                break

            article = {
                "platform": "news",
                "keyword": keyword,
                "title": item.find("title").text if item.find("title") is not None else "",
                "description": item.find("description").text if item.find("description") is not None else "",
                "link": item.find("link").text if item.find("link") is not None else "",
                "published_date": item.find("pubDate").text if item.find("pubDate") is not None else "",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            all_articles.append(article)
            count += 1

    return all_articles
