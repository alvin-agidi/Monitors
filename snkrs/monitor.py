import asyncio
import logging
import time
import traceback
from datetime import datetime, timezone

import aiohttp
import requests as rq
import urllib3
from config import AVATAR_URL, DELAY, KEYWORDS, USERNAME, WEBHOOK_URL
from discord import Embed, Webhook

import snkrs.fetch as fetch
from globalConfig import (
    CURRENCY_SYMBOLS,
    ENABLE_FREE_PROXY,
    LANGUAGE,
    LOCATION,
    STANDARD_LOCATIONS,
    create_proxies,
    create_proxy_obj,
    create_user_agent,
    create_user_agent_rotator,
    rotate_proxies,
)
from globalConfig import SNEAK_CRED_GREEN as COLOUR

KEYWORDS = [keyword.lower() for keyword in KEYWORDS]
CURRENCY_SYMBOL = CURRENCY_SYMBOLS[LOCATION] if LOCATION in CURRENCY_SYMBOLS else ""

logging.basicConfig(
    filename="snkrs/monitor.log",
    filemode="w",
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
            "description": product["description"],
            "url": product["url"],
            "thumbnail": {"url": product["thumbnail"]},
            "color": COLOUR,
            "footer": {"text": "Sneak Cred"},
            "timestamp": str(datetime.now(timezone.utc)),
            "fields": [
                {
                    "name": "Price",
                    "value": CURRENCY_SYMBOL + product["price"],
                    "inline": True,
                },
                {"name": "Style Code", "value": product["style_code"], "inline": True},
                {
                    "name": "Release Method",
                    "value": product["release_method"],
                    "inline": True,
                },
                {
                    "name": "Release Date",
                    "value": "<t:"
                    + product["release_date"]
                    + ":F>\n"
                    + "(<t:"
                    + product["release_date"]
                    + ":R>)",  # ,
                    "inline": True,
                },
                {"name": "Region", "value": product["region"], "inline": True},
                {
                    "name": "Exclusive Access",
                    "value": product["exclusive_access"],
                    "inline": True,
                },
                {"name": "Sizes", "value": product["sizes"]},
            ],
        }
    )

    await webhook.send(embed=embed, username=USERNAME, avatar_url=AVATAR_URL)

    msg = product["title"] + " successfully sent."
    print(msg)
    logging.info(msg=msg)


async def monitor():
    """
    Initiates the monitor
    """
    msg = "\n---------------------------------\n--- SNKRS MONITOR HAS STARTED ---\n---------------------------------\n"
    print(msg)
    logging.info(msg=msg)

    # Ensures that first scrape does not notify all products
    start = True

    user_agent_rotator = create_user_agent_rotator()
    user_agent = create_user_agent(user_agent_rotator)
    proxy_obj = create_proxy_obj() if ENABLE_FREE_PROXY else None
    proxies, proxy_no = create_proxies(proxy_obj)

    if LOCATION in STANDARD_LOCATIONS:
        fetch_new_products = fetch.fetch_new_products
    elif LOCATION == "CL":
        fetch_new_products = fetch.fetch_new_products_chile
    elif LOCATION == "BR":
        fetch_new_products = fetch.fetch_new_products_brazil
    else:
        print(
            f'LOCATION "{LOCATION}" CURRENTLY NOT AVAILABLE. IF YOU BELIEVE THIS IS A MISTAKE PLEASE CREATE AN ISSUE ON GITHUB OR MESSAGE THE #issues CHANNEL IN DISCORD.'
        )
        return

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(WEBHOOK_URL, session=session)
        while True:
            try:
                new_products = fetch_new_products(
                    INSTOCK,
                    LOCATION,
                    LANGUAGE,
                    user_agent,
                    proxies,
                    KEYWORDS,
                    start,
                )
                for product in new_products:
                    await send_to_discord(product, webhook)

            except rq.exceptions.RequestException as e:
                logging.error(e)
                logging.info("Rotating proxy")

                proxy, proxy_no = rotate_proxies(proxy_obj, proxy_no)
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
