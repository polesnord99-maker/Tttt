"""Configuration du bot."""
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
TIMEZONE_NAME = os.getenv("TIMEZONE", "Europe/Brussels").strip()
try:
    TIMEZONE = ZoneInfo(TIMEZONE_NAME)
except ZoneInfoNotFoundError as exc:
    raise RuntimeError(f"Fuseau horaire inconnu : {TIMEZONE_NAME}") from exc
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID", "0") or 0)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/entreprise_bot.sqlite3")
