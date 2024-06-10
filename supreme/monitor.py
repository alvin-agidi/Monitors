import asyncio
import json
import logging
import time
import traceback
from datetime import datetime, timezone

import aiohttp
import requests
import urllib3
from bs4 import BeautifulSoup
from config import AVATAR_URL, DELAY, KEYWORDS, USERNAME, WEBHOOK_URL
from discord import Embed, Webhook

from globalConfig import CURRENCY_SYMBOLS, ENABLE_FREE_PROXY, LOCATION
from globalConfig import SNEAK_CRED_GREEN as COLOUR
from globalConfig import (
    create_headers,
    create_proxy,
    create_proxy_obj,
    create_user_agent_rotator,
    rotate_headers,
    rotate_proxy,
)

KEYWORDS = [keyword.lower() for keyword in KEYWORDS]
CURRENCY_SYMBOL = CURRENCY_SYMBOLS[LOCATION] if LOCATION in CURRENCY_SYMBOLS else ""

logging.basicConfig(
    filename="supreme-monitor.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(message)s",
    level=logging.DEBUG,
)

INSTOCK = []


async def send_to_discord(product, webhook):
    """
    Sends a Discord webhook notification to the specified webhook URL
    """
    embed = Embed.from_dict(
        {
            "title": product["title"],
            "description": product["color"],
            "thumbnail": {"url": product["thumbnail"]},
            "url": product["url"],
            "color": COLOUR,
            "footer": {"text": "Sneak Cred"},
            "timestamp": str(datetime.now(timezone.utc)),
            "fields": [
                {"name": "Price", "value": CURRENCY_SYMBOL + product["price"]},
                {"name": "Sizes", "value": product["sizes"]},
            ],
        }
    )

    try:
        await webhook.send(embed=embed, username=USERNAME, avatar_url=AVATAR_URL)
    except Exception as e:
        print(e)
    else:
        msg = product["title"] + " successfully sent."
        print(msg)
        logging.info(msg=msg)


def fetch_new_products(products, start):
    new_products = []
    for item in products:
        if not KEYWORDS or any(
            key.lower() in item["title"].lower() for key in KEYWORDS
        ):
            sizes = [
                variant["title"] + "\n"
                for variant in item["variants"]
                if variant["available"]
            ]

            item_id = item["id"]

            if sizes and item_id not in INSTOCK:
                INSTOCK.append(item_id)
                if not start:
                    new_products.append(
                        dict(
                            title=item["title"],
                            price=format(item["price"] / 100, ".2f"),
                            thumbnail="https:" + item["image"],
                            sizes="".join(sizes),
                            color=item["color"],
                            url="https://uk.supreme.com" + item["url"],
                        )
                    )
            elif not sizes and item_id in INSTOCK:
                INSTOCK.remove(item_id)

    return new_products


def scrape_site(headers, proxy):
    url = "https://uk.supreme.com/collections/all"

    html = requests.get(url, headers=headers, proxies=proxy)
    soup = BeautifulSoup(html.text, "html.parser")

    content = soup.find("script", {"id": "products-json"})
    products = json.loads(content.text)["products"]

    return products


async def monitor():
    """
    Initiates the monitor
    """
    msg = "\n-----------------------------------\n--- SUPREME MONITOR HAS STARTED ---\n-----------------------------------\n"
    print(msg)
    logging.info(msg=msg)

    # Ensures that first scrape does not notify all products
    start = False

    user_agent_rotator = create_user_agent_rotator()
    headers = create_headers(user_agent_rotator)
    proxy_obj = create_proxy_obj() if ENABLE_FREE_PROXY else None
    proxy, proxy_no = create_proxy(proxy_obj)

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(WEBHOOK_URL, session=session)
        while True:
            try:
                # Makes request to site and stores products
                products = scrape_site(proxy, headers)
                new_products = fetch_new_products(products, start)

                for product in new_products:
                    await send_to_discord(product, webhook)

            except requests.exceptions.RequestException as e:
                logging.error(e)
                logging.info("Rotating headers and proxy")

                headers = rotate_headers(headers, user_agent_rotator)
                proxy, proxy_no = rotate_proxy(proxy_obj, proxy_no)
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
