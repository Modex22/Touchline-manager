import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Server port for Render web service health checks
PORT = int(os.getenv("PORT", "10000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Webhook configuration (optional - if WEBHOOK_URL is set, uses webhooks, otherwise polling + health server)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "touchline_secret")

# Database path
DATA_DIR = os.getenv("DATA_DIR", "data")
DATABASE_PATH = os.path.join(DATA_DIR, "touchline.db")
LOGOS_DIR = os.path.join(DATA_DIR, "logos")

# Ensure storage directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGOS_DIR, exist_ok=True)

# Game constants
STARTING_BUDGET = 25_000_000  # €25,000,000 for new clubs
DEFAULT_STADIUM_CAPACITY = 25_000
TICKET_PRICE = 35  # Average ticket price in €
MAX_SQUAD_SIZE = 25
MIN_SQUAD_SIZE = 14
