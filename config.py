import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN    = os.getenv("BOT_TOKEN", "")
CHANNEL_ID   = os.getenv("CHANNEL_ID", "")        # @canal ou -100...
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/suporte_laricontas")
WEBAPP_URL   = os.getenv("WEBAPP_URL", "")
BANNER_URL   = os.getenv("BANNER_URL", "")

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

DATABASE_PATH = os.getenv("DATABASE_PATH", "larizinha.db")
