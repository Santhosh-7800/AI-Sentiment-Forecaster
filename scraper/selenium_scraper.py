from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time


def scrape_reviews(url, platform="amazon"):

    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    reviews = []

    # Amazon example selector
    for review in soup.select(".review-text-content"):
        reviews.append({
            "platform": platform,
            "text": review.get_text(strip=True)
        })

    return reviews
# # scraper/category_scraper.py

# from selenium import webdriver

# import time


def get_product_links(category_url, max_products=5):

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)

    driver.get(category_url)
    time.sleep(5)  # allow page to load

    product_links = []

    # Amazon product links usually contain '/dp/'
    elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/dp/')]")

    for element in elements:
        link = element.get_attribute("href")

        if link and "/dp/" in link:
            clean_link = link.split("?")[0]
            product_links.append(clean_link)

    driver.quit()

    # Remove duplicates
    unique_links = list(set(product_links))

    return unique_links[:max_products]
