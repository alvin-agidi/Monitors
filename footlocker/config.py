from globalConfig import SNEAK_CRED_GREEN

# --------------------- WEBHOOK URL ---------------------
WEBHOOK = ""

# --------------------- LOCATIONS ---------------------
# Current available locations [US, UK, AU]
LOCATION = ""

# --------------------- FREE PROXY ---------------------
# A single or multiple locations can be added in the array (e.g. ["GB"] or ["GB", "US"])
ENABLE_FREE_PROXY = False
FREE_PROXY_LOCATION = ["GB"]

# --------------------- DELAY ---------------------
# Delay between site requests
DELAY = 5

# --------------------- OPTIONAL PROXY ---------------------
# Proxies must follow this format: "<proxy>:<port>" OR "<proxy_username>:<proxy_password>@<proxy_domain>:<port>")
# If you want to use multiple proxies, please create an array
# E.G. PROXY = ["proxy1:proxy1port", "proxy2:proxy2port"]
PROXY = []

# --------------------- OPTIONAL KEYWORDS ---------------------
# E.G. KEYWORDS = ["box","logo"]
KEYWORDS = []

# --------------------- DISCORD BOT FEATURES ---------------------
USERNAME = "Footlocker"
AVATAR_URL = "https://raw.githubusercontent.com/yasserqureshi1/Sneaker-Monitors/master/monitors/footlocker/logo.jpg"
COLOUR = SNEAK_CRED_GREEN
