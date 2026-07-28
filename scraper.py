import requests
from bs4 import BeautifulSoup
import re

def get_price_and_stock(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        html = str(soup)

        # Price extract
        price = None
        price_match = re.search(r'["₹]?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?=["\s]*<\/\w+>(?:<\/\w+>)*\s*(?:price|₹|buy))', html)
        if price_match:
            price_str = re.sub(r'[^\d.]', '', price_match.group())
            if price_str:
                price = float(price_str)

        # Stock check
        in_stock = False
        stock_keywords = ['in stock', 'available', 'instock', 'buy now', 'add to cart']
        if any(keyword in html.lower() for keyword in stock_keywords):
            in_stock = True

        return {
            "price": price,
            "in_stock": in_stock
        }
    except Exception as e:
        print("Error scraping:", e)
        return None
