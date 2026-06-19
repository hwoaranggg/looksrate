import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]

# Кол-во бесплатных анализов
FREE_ANALYSES: int = 2

# Стоимость одного анализа в Stars
STARS_PER_ANALYSIS: int = 5
STARS_DETAILED: int = 10  # расширенный разбор

# SQLite путь
DB_PATH: str = "lookmaxbot.db"
