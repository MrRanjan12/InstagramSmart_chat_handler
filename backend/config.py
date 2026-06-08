from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class Config:
    # =========================
    # Instagram / Meta
    # =========================
    INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")
    INSTAGRAM_VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN")
    PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

    INSTAGRAM_PAGE_ID = os.getenv("INSTAGRAM_PAGE_ID")
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

    # =========================
    # AI PROVIDERS
    # =========================

    # Groq (PRIMARY - recommended)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile"
    )

    # OpenAI (optional fallback)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # =========================
    # BOT SETTINGS
    # =========================
    BOT_NAME = os.getenv("BOT_NAME", "Instagram Assistant")

    AUTO_REPLY = os.getenv("AUTO_REPLY", "true").lower() == "true"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    REPLY_DELAY_SECONDS = int(os.getenv("REPLY_DELAY_SECONDS", 2))
    MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", 10))

    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
    POLITE_MODE = os.getenv("POLITE_MODE", "true").lower() == "true"

    # =========================
    # SERVER
    # =========================
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # =========================
    # LOGGING
    # =========================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

    # =========================
    # DATABASE
    # =========================
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///db/conversations.db"
    )


config = Config()