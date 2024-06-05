import aiohttp
from random_user_agent.params import SoftwareName, HardwareType
from random_user_agent.user_agent import UserAgent

import requests as rq
import urllib3
from fp.fp import FreeProxy

from datetime import datetime, timezone
import time

import json
import logging
import traceback
from discord import Webhook
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


INSTOCK = []


async def sendToDiscord(
    webhook, title, description, url, thumbnail, price, style_code, sizes
):
    """
    Sends a Discord webhook notification to the specified webhook URL
    """
    content = {
        "title": title,
        "description": description,
        "url": url,
        "thumbnail": {"url": thumbnail},
        "color": int(COLOUR),
        "footer": {"text": "Sneak Cred"},
        "timestamp": str(datetime.now(timezone.utc)),
        "fields": [
            {"name": "Price", "value": price},
            {"name": "Style Code", "value": style_code},
            {"name": "Sizes", "value": sizes},
        ],
    }

    await webhook.send(
        content=json.dumps(content), username=USERNAME, avatar_urL=AVATAR_URL
    )

    # try:
    # result.raise_for_status()
    # except rq.exceptions.HTTPError as err:
    #     logging.error(msg=err)
    # else:
    print("Payload delivered successfully, code {}.".format(result.status_code))
    logging.info(
        msg="Payload delivered successfully, code {}.".format(result.status_code)
    )


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
                if LOCATION in locations.___standard_api___:
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
                    sendToDiscord(
                        webhook,
                        product["title"],
                        product["description"],
                        product["url"],
                        product["thumbnail"],
                        product["price"],
                        product["style_code"],
                        product["sizes"],
                    )
                    print(product["title"])

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
