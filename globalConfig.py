from random_user_agent.params import SoftwareName, HardwareType
from random_user_agent.user_agent import UserAgent
from fp.fp import FreeProxy

SNEAK_CRED_GREEN = 0x26B062

LOCATION = "GB"
LANGUAGE = "en-GB"

# --------------------- FREE PROXY ---------------------
# A single or multiple locations can be added in the array (e.g. ["GB"] or ["GB", "US"])
ENABLE_FREE_PROXY = True
FREE_PROXY_LOCATION = ["GB"]

SOFTWARE_NAMES = [SoftwareName.CHROME.value]
HARDWARE_TYPE = [HardwareType.MOBILE__PHONE]

# --------------------- OPTIONAL PROXY ---------------------
# Proxies must follow this format: "<proxy>:<port>" OR "<proxy_username>:<proxy_password>@<proxy_domain>:<port>")
# If you want to use multiple proxies, please create an array
# E.G. PROXY = ["proxy1:proxy1port", "proxy2:proxy2port"]
PROXY = []

STANDARD_LOCATIONS = [
    "GB",
    "US",
    "AU",
    "AT",
    "BE",
    "BG",
    "CA",
    "CN",
    "HR",
    "CZ",
    "DK",
    "EG",
    "FI",
    "FR",
    "DE",
    "HU",
    "IN",
    "ID",
    "IE",
    "IT",
    "MY",
    "MX",
    "MA",
    "NL",
    "NZ",
    "NO",
    "PH",
    "PL",
    "PT",
    "PR",
    "RO",
    "RU",
    "SA",
    "SG",
    "SI",
    "ZA",
    "ES",
    "SE",
    "CH",
    "TR",
    "AE",
    "VN",
    "JP",
]

CURRENCY_SYMBOLS = {"GB": "£"}


def create_user_agent_rotator():
    return UserAgent(software_names=SOFTWARE_NAMES, hardware_type=HARDWARE_TYPE)


def create_headers(user_agent_rotator):
    return {
        "user-agent": user_agent_rotator.get_random_user_agent(),
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }


def create_proxy_obj():
    return FreeProxy(country_id=FREE_PROXY_LOCATION, rand=True)


def create_proxy(proxy_obj):
    if ENABLE_FREE_PROXY:
        proxy = {"http": proxy_obj.get()}
    elif PROXY != []:
        proxy_no = 0
        proxy = (
            {} if PROXY == [] else {"http": PROXY[proxy_no], "https": PROXY[proxy_no]}
        )
    else:
        proxy = {}

    return proxy


def rotate_headers(headers, user_agent_rotator):
    headers["User-Agent"] = user_agent_rotator.get_random_user_agent()


def rotate_proxy(proxy_obj):
    if ENABLE_FREE_PROXY:
        proxy = {"http": proxy_obj.get()}
    elif PROXY != []:
        proxy_no = 0 if proxy_no == (len(PROXY) - 1) else proxy_no + 1
        proxy = {"http": PROXY[proxy_no], "https": PROXY[proxy_no]}

    return proxy
