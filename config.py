import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CANAL_ID = os.getenv("CANAL_ID")        # ex: @LarizinhaStore ou -100xxxxxxxxx
CANAL_LINK = os.getenv("CANAL_LINK")    # ex: https://t.me/LarizinhaStore
