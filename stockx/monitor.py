"""The stockx shoe crawler loads into page 1 of stockx/sneakers, goes into every shoe link, and extracts the shoe name,
retail price, average sale price, and the url to its picture. The crawler will continue until a specified number of
pages have been scraped"""

# import csv
import asyncio
import json
import logging
import re
import time
import traceback
import aiohttp
import requests as rq
import urllib3
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from config import DELAY, KEYWORDS, WEBHOOK_URL
from discord import Embed, Webhook
from tqdm.auto import tqdm

from globalConfig import (
    CURRENCY_SYMBOLS,
    ENABLE_FREE_PROXY,
    LANGUAGE,
    LOCATION,
    STANDARD_LOCATIONS,
    create_headers,
    create_proxies,
    create_proxy_obj,
    create_user_agent,
    create_user_agent_rotator,
    rotate_headers,
    rotate_proxies,
)
from globalConfig import SNEAK_CRED_GREEN as COLOUR

KEYWORDS = [keyword.lower() for keyword in KEYWORDS]
CURRENCY_SYMBOL = CURRENCY_SYMBOLS[LOCATION] if LOCATION in CURRENCY_SYMBOLS else ""

logging.basicConfig(
    filename="stockx/monitor.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(message)s",
    level=logging.DEBUG,
)

headers = {
    "accept": "application/json",
    "accept-encoding": "utf-8",
    "accept-language": "en-GB,en;q=0.9",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
    "x-requested-with": "XMLHttpRequest",
    "app-platform": "Iron",
    "app-version": "2022.05.08.04",
    "referer": "https://stockx.com/",
}

EXISTING_PRODUCTS = []


async def send_product(product, webhook):
    """
    Sends a Discord webhook notification to the specified webhook URL
    """
    embed = Embed.from_dict(
        {
            "title": product["title"],
            # "description": product["color"],
            "thumbnail": {"url": product["thumbnail"]},
            "url": product["url"],
            "color": COLOUR,
            "footer": {"text": "Sneak Cred"},
            "timestamp": str(datetime.now(timezone.utc)),
            "fields": [
                {
                    "Retail": CURRENCY_SYMBOL + product["retail"],
                    "Last Sale": CURRENCY_SYMBOL + product["last_sale"],
                    "Average Sale": CURRENCY_SYMBOL + product["avg_sale"],
                    "Average Profit": CURRENCY_SYMBOL + product["avg_profit"],
                },
                {"name": "Sizes", "value": product["sizes"]},
            ],
        }
    )

    await webhook.send(embed=embed)

    msg = product["title"] + " successfully sent."
    print(msg)
    logging.info(msg=msg)


def fetch_new_products(EXISTING_PRODUCTS, start, headers, proxies):
    new_products = []
    max_pages = 1
    page = 1

    # loop through each item of each page to scrape data until until max page
    while page <= max_pages:
        url = "https://stockx.com/en-gb/sneakers?page=" + str(page)

        # request the url text and create BeautifulSoup object to parse html
        source_code = requests.get(
            url, headers=headers, proxies=proxies, allow_redirects=True
        )
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text, "lxml")
        print(soup)

        # parses through each shoe on the page to scrape the data
        for link in tqdm(soup.findAll("div", {"class": "tile browse-tile false"})):
            shoe = link.a
            href = "https://stockx.com/en-gb/" + shoe.get("href")
            print(href)

            if start or href not in EXISTING_PRODUCTS:
                product = fetch_product(href)
                avg_profit = product["retail"] - product["avg_sale"]
                if start or True:
                    new_products.append({*product, avg_profit})

        print("{}/{} page(s) have been crawled!".format(page, max_pages))

        page += 1

    print("All {} page(s) have been scraped!".format(max_pages))

    return new_products


def fetch_product(url, headers, proxies):
    source_code = requests.get(url, headers=headers, proxies=proxies)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, "lxml")

    return {
        title,
        thumbnail,
        retail,
        last_sale,
        avg_sale,
        url,
    }


async def monitor():
    start = True

    user_agent_rotator = create_user_agent_rotator()
    global headers
    headers["user-agent"] = user_agent_rotator.get_random_user_agent()
    proxy_obj = create_proxy_obj() if ENABLE_FREE_PROXY else None
    proxies, proxy_no = create_proxies(proxy_obj)

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(WEBHOOK_URL, session=session)
        while start:
            try:
                new_products = fetch_new_products(
                    EXISTING_PRODUCTS, start, headers, proxies
                )
                for product in new_products:
                    await send_product(product, webhook)

            except requests.exceptions.RequestException as e:
                logging.error(e)
                logging.info("Rotating headers and proxy")

                headers = rotate_headers(headers, user_agent_rotator)
                proxies, proxy_no = rotate_proxies(proxy_obj, proxy_no)

            except Exception as e:
                print(f"Exception found: {traceback.format_exc()}")
                logging.error(e)

            # Allows changes to be notified
            start = False

            # User set delay
            time.sleep(float(DELAY))


if __name__ == "__main__":
    urllib3.disable_warnings()
    asyncio.run(monitor())
