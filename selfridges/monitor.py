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

KEYWORDS = [keyword.lower() for keyword in KEYWORDS]
CURRENCY_SYMBOL = CURRENCY_SYMBOLS[LOCATION] if LOCATION in CURRENCY_SYMBOLS else ""

logging.basicConfig(
    filename="selfridges/monitor.log",
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
                {
                    "name": "Price",
                    "value": CURRENCY_SYMBOL + product["price"],
                },
                {"name": "Sizes", "value": product["sizes"]},
            ],
        }
    )

    await webhook.send(embed=embed, username=USERNAME, avatar_url=AVATAR_URL)

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
                            url="https://www.selfridges.com" + item["url"],
                        )
                    )
            elif not sizes and item_id in INSTOCK:
                INSTOCK.remove(item_id)

    return new_products


# def scrape_site(headers, proxy):
# url = "https://www.selfridges.com/GB/en/cat/mens/on_sale/alexander-mcqueen/amiri/axel-arigato/balenciaga/burberry/balmain/billionaire-boys-club/bvlgari/comme-des-garcons/comme-des-garcons-play/cp-company/dickies/dolce-gabbana/diesel/dsquared2/fear-of-god-essentials/gallery-dept/kenzo/givenchy/jordan/emporio-armani/icecream/moncler/off-white-c-o-virgil-abloh/patagonia/prada/giorgio-armani/fendi/lanvin/lacoste/represent/market/palm-angels/rick-owens/tom-ford/versace/timberland/valentino-garavani/a-bathing-ape/cartier/oakley/nike/polo-ralph-lauren/carhartt-wip/adidas/common-projects/fear-of-god/vivienne-westwood/?fh_sort_by=price_asc&pn=1"

# html = requests.get(url, headers=headers, proxies=proxies)
# print(html)
# soup = BeautifulSoup(html.text, "html.parser")
# print(soup)

# content = soup.find("script", {"id": "products-json"})
# products = json.loads(content.text)["products"]
# return products

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def scrape_site(headers, proxy):
    # Set up options for headless Chrome
    # options = Options()
    # options.headless = True  # Enable headless mode for invisible operation
    # options.add_argument("--window-size=1920,1200")

    # Initialize Chrome with the specified options
    options = webdriver.ChromeOptions()
    options.headless = True
    options.binary_location = ""
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = uc.Chrome(options=options, use_subprocess=True)
    # driver = uc.Chrome(use_subprocess=True)
    driver.get(
        "https://www.selfridges.com/GB/en/cat/mens/on_sale/alexander-mcqueen/amiri/axel-arigato/balenciaga/burberry/balmain/billionaire-boys-club/bvlgari/comme-des-garcons/comme-des-garcons-play/cp-company/dickies/dolce-gabbana/diesel/dsquared2/fear-of-god-essentials/gallery-dept/kenzo/givenchy/jordan/emporio-armani/icecream/moncler/off-white-c-o-virgil-abloh/patagonia/prada/giorgio-armani/fendi/lanvin/lacoste/represent/market/palm-angels/rick-owens/tom-ford/versace/timberland/valentino-garavani/a-bathing-ape/cartier/oakley/nike/polo-ralph-lauren/carhartt-wip/adidas/common-projects/fear-of-god/vivienne-westwood/?fh_sort_by=price_asc&pn=1"
    )

    # Output the page source to the console
    print(driver.page_source)
    # Close the browser session cleanly to free up system resources
    driver.quit()

    return []


async def monitor():
    """
    Initiates the monitor
    """
    msg = "\n--------------------------------------\n--- SELFRIDGES MONITOR HAS STARTED ---\n--------------------------------------\n"
    print(msg)
    logging.info(msg=msg)

    # Ensures that first scrape does not notify all products
    start = True

    user_agent_rotator = create_user_agent_rotator()
    headers = create_headers(user_agent_rotator)
    proxy_obj = create_proxy_obj() if ENABLE_FREE_PROXY else None
    proxies, proxy_no = create_proxies(proxy_obj)

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(WEBHOOK_URL, session=session)
        while True:
            try:
                # Makes request to site and stores products
                products = scrape_site(proxies, headers)
                new_products = fetch_new_products(products, start)

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
