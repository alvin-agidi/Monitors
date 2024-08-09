import asyncio
import logging
import time
import traceback
import aiohttp

import urllib3
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from config import AVATAR_URL, DELAY, KEYWORDS, USERNAME, WEBHOOK_URL
from discord import Embed, Webhook

from globalConfig import (
    CURRENCY_SYMBOLS,
    ENABLE_FREE_PROXY,
    LANGUAGE,
    LOCATION,
    STANDARD_LOCATIONS,
    create_headers,
    create_proxies,
    create_proxy_obj,
    create_user_agent_rotator,
    rotate_headers,
    rotate_proxies,
)
from globalConfig import SNEAK_CRED_GREEN as COLOUR

KEYWORDS = [keyword.lower() for keyword in KEYWORDS]
CURRENCY_SYMBOL = CURRENCY_SYMBOLS[LOCATION] if LOCATION in CURRENCY_SYMBOLS else ""

logging.basicConfig(
    filename="houseoffraser/monitor.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(message)s",
    level=logging.DEBUG,
)

EXISTING_SIZES = []

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
}


async def send_to_discord(product, webhook):
    """
    Sends a Discord webhook notification to the specified webhook URL
    """
    embed = Embed.from_dict(
        {
            "title": product["title"],
            "description": product["description"],
            "thumbnail": {"url": product["thumbnail"]},
            "url": product["url"],
            "color": COLOUR,
            "footer": {"text": "Sneak Cred"},
            "timestamp": str(datetime.now(timezone.utc)),
            "fields": [
                {"name": "Price", "value": product["price"], "inline": True},
                {"name": "Size", "value": product["size"]},
            ],
        }
    )

    await webhook.send(embed=embed, username=USERNAME, avatar_url=AVATAR_URL)

    msg = product["title"] + " (" + product["size"] + ") successfully sent."
    print(msg)
    logging.info(msg=msg)


def fetch_new_sizes(start, headers, proxies):
    global EXISTING_SIZES
    new_sizes = []
    url = "https://www.houseoffraser.co.uk/brand/timberland/6-inch-premium-boots-182098"

    source_code = requests.get(
        url, headers=headers, proxies=proxies, allow_redirects=True
    )
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, "html.parser")

    title = (
        soup.find("span", {"id": "lblProductBrand"}).get_text().strip()
        + " "
        + soup.find("span", {"id": "lblProductName"}).get_text()
    )
    desc = soup.find("span", {"id": "colourName"}).get_text().strip()
    price = soup.find("span", {"id": "lblSellingPrice"}).get_text()
    thumbnail = soup.find("img", {"id": "imgProduct"}).get("src")

    instock_sizes = [
        size_element.get("data-text").split("(")[0].split()[0]
        for size_element in soup.findAll("li", {"class": "tooltip sizeButtonli"})
    ]

    for size in instock_sizes:
        if not start and size not in EXISTING_SIZES:
            new_sizes.append(
                {
                    "url": url,
                    "title": title,
                    "description": desc,
                    "thumbnail": thumbnail,
                    "price": price,
                    "size": size,
                }
            )

    EXISTING_SIZES = instock_sizes

    return new_sizes


async def monitor():
    start = False

    user_agent_rotator = create_user_agent_rotator()
    global headers
    headers["user-agent"] = user_agent_rotator.get_random_user_agent()
    proxy_obj = create_proxy_obj() if ENABLE_FREE_PROXY else None
    proxies, proxy_no = create_proxies(proxy_obj)

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(WEBHOOK_URL, session=session)
        while True:
            try:
                new_products = fetch_new_sizes(start, headers, proxies)
                for product in new_products:
                    await send_to_discord(product, webhook)

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
