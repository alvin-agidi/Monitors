import aiohttp
from random_user_agent.params import SoftwareName, HardwareType
from random_user_agent.user_agent import UserAgent

import requests as rq
import urllib3
from fp.fp import FreeProxy

from datetime import datetime, timezone
import time

import logging
import traceback
from discord import Webhook, Embed
import asyncio

import locations

from config import (
    WEBHOOK_URL,
    DELAY,
    KEYWORDS,
    USERNAME,
    AVATAR_URL,
)

from globalConfig import (
    LOCATION,
    LANGUAGE,
    ENABLE_FREE_PROXY,
    FREE_PROXY_LOCATION,
    STANDARD_LOCATIONS,
    CURRENCY_SYMBOLS,
    PROXY,
    SNEAK_CRED_GREEN as COLOUR,
)

logging.basicConfig(
    filename="snkrs-monitor.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(message)s",
    level=logging.DEBUG,
)

software_names = [SoftwareName.CHROME.value]
hardware_type = [HardwareType.MOBILE__PHONE]
user_agent_rotator = UserAgent(
    software_names=software_names, hardware_type=hardware_type
)

if ENABLE_FREE_PROXY:
    proxy_obj = FreeProxy(country_id=FREE_PROXY_LOCATION, rand=True)

KEYWORDS = [keyword.lower() for keyword in KEYWORDS]
CURRENCY_SYMBOL = CURRENCY_SYMBOLS[LOCATION] if LOCATION in CURRENCY_SYMBOLS else ""

INSTOCK = []


async def send_to_discord(webhook, product):
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
                    + str(
                        int(
                            datetime.strptime(
                                product["release_date"], "%Y-%m-%dT%H:%M:%S.%fZ"
                            ).timestamp()
                        )
                    )
                    + ":F>\n"
                    + "(<t:"
                    + str(
                        int(
                            datetime.strptime(
                                product["release_date"], "%Y-%m-%dT%H:%M:%S.%fZ"
                            ).timestamp()
                        )
                    )
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
    try:
        await webhook.send(embed=embed, username=USERNAME, avatar_url=AVATAR_URL)
    except Exception as e:
        print(e)
    else:
        msg = product["title"] + " successfully sent."
        print(msg)
        logging.info(msg=msg)


async def monitor():
    """
    Initiates the monitor
    """
    print(
        """\n---------------------------------
--- SNKRS MONITOR HAS STARTED ---
---------------------------------\n"""
    )
    logging.info(msg="Successfully started monitor")

    # Ensures that first scrape does not notify all products
    start = False

    # Initialising proxy and headers
    if ENABLE_FREE_PROXY:
        proxy = {"http": proxy_obj.get()}
    elif PROXY != []:
        proxy_no = 0
        proxy = (
            {} if PROXY == [] else {"http": PROXY[proxy_no], "https": PROXY[proxy_no]}
        )
    else:
        proxy = {}
    user_agent = user_agent_rotator.get_random_user_agent()

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(WEBHOOK_URL, session=session)
        while True:
            try:
                if LOCATION in STANDARD_LOCATIONS:
                    new_products = locations.standard_api(
                        INSTOCK, LOCATION, LANGUAGE, user_agent, proxy, KEYWORDS, start
                    )
                elif LOCATION == "CL":
                    new_products = locations.chile(
                        INSTOCK, LOCATION, LANGUAGE, user_agent, proxy, KEYWORDS, start
                    )
                elif LOCATION == "BR":
                    new_products = locations.brazil(
                        INSTOCK, LOCATION, LANGUAGE, user_agent, proxy, KEYWORDS, start
                    )
                else:
                    print(
                        f'LOCATION "{LOCATION}" CURRENTLY NOT AVAILABLE. IF YOU BELIEVE THIS IS A MISTAKE PLEASE CREATE AN ISSUE ON GITHUB OR MESSAGE THE #issues CHANNEL IN DISCORD.'
                    )
                    return

                for product in new_products:
                    await send_to_discord(webhook, product)

            except rq.exceptions.RequestException as e:
                logging.error(e)
                logging.info("Rotating headers and proxy")

                # Rotates headers
                user_agent = user_agent_rotator.get_random_user_agent()

                if ENABLE_FREE_PROXY:
                    proxy = {"http": proxy_obj.get()}

                elif PROXY != []:
                    proxy_no = 0 if proxy_no == (len(PROXY) - 1) else proxy_no + 1
                    proxy = {"http": PROXY[proxy_no], "https": PROXY[proxy_no]}

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
