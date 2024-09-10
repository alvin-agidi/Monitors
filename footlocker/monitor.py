import json
import logging
import time
import traceback
from datetime import datetime, timezone
from discord import Embed, Webhook
import asyncio

import aiohttp
import urllib3

import requests
from config import DELAY, KEYWORDS, WEBHOOK_URL

from globalConfig import (
    CURRENCY_SYMBOLS,
    ENABLE_FREE_PROXY,
    LOCATION,
    create_headers,
    create_proxies,
    create_proxy_obj,
    create_user_agent_rotator,
    rotate_headers,
    rotate_proxies,
)
from globalConfig import SNEAK_CRED_GREEN as COLOUR


from locations import (
    fetch_new_products_AU,
    fetch_new_products_GB,
    fetch_new_products_US,
)

KEYWORDS = [keyword.lower() for keyword in KEYWORDS]
CURRENCY_SYMBOL = CURRENCY_SYMBOLS[LOCATION] if LOCATION in CURRENCY_SYMBOLS else ""

logging.basicConfig(
    filename="footlocker/monitor.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(message)s",
    level=logging.DEBUG,
)

INSTOCK = []


async def send_product(product, webhook):
    """
    Sends a Discord webhook notification to the specified webhook URL
    """
    embed = {
        "title": product["title"],
        "url": product["url"],
        "thumbnail": {"url": product["thumbnail"]},
        "footer": {"text": "Sneak Cred"},
        "timestamp": str(datetime.now(timezone.utc)),
        "color": COLOUR,
        "fields": [
            {"name": "Price", "value": product["price"], "inline": True},
            {"name": "SKU", "value": product["sku"], "inline": True},
        ],
    }

    await webhook.send(embed=embed, username=USERNAME, avatar_url=AVATAR_URL)

    msg = product["title"] + " successfully sent."
    print(msg)
    logging.info(msg=msg)


async def monitor():
    msg = "\n--------------------------------------\n--- FOOTLOCKER MONITOR HAS STARTED ---\n--------------------------------------\n"
    print(msg)
    logging.info(msg=msg)

    # Ensures that first scrape does not notify all products
    start = 1

    user_agent_rotator = create_user_agent_rotator()
    headers = create_headers(user_agent_rotator)
    proxy_obj = create_proxy_obj() if ENABLE_FREE_PROXY else None
    proxies, proxy_no = create_proxies(proxy_obj)

    if LOCATION == "US":
        fetch_new_products = fetch_new_products_US
    elif LOCATION == "GB":
        fetch_new_products = fetch_new_products_GB
    elif LOCATION == "AU":
        fetch_new_products = fetch_new_products_AU
    else:
        print(
            "LOCATION CURRENTLY NOT AVAILABLE. IF YOU BELIEVE THIS IS A MISTAKE PLEASE CREATE AN ISSUE ON GITHUB OR MESSAGE THE #issues CHANNEL IN DISCORD."
        )
        return

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(WEBHOOK_URL, session=session)
        while True:
            try:
                new_products = fetch_new_products(
                    INSTOCK, user_agent_rotator, proxies, KEYWORDS, start
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
