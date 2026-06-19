from fastapi import FastAPI

from config import config
from webhook import router as webhook_router

from database import Base
from database import engine

# Import models so SQLAlchemy can create tables
from models.user import User
from models.conversation import Conversation
from models.message import Message


APP_VERSION = "2.0.0"

app = FastAPI(
    title="Instagram AI Assistant",
    version=APP_VERSION
)

app.include_router(webhook_router)


@app.on_event("startup")
async def startup_event():

    Base.metadata.create_all(bind=engine)

    print("=" * 60)
    print(f"{config.BOT_NAME} started successfully 🚀")
    print(f"Auto Reply: {config.AUTO_REPLY}")
    print(f"Debug Mode: {config.DEBUG}")
    print("=" * 60)


@app.get("/")
async def home():

    return {
        "service": config.BOT_NAME,
        "status": "running",
        "version": APP_VERSION
    }


@app.get("/health")
async def health_check():

    return {
        "status": "healthy",
        "service": config.BOT_NAME,
        "version": APP_VERSION
    }


if config.DEBUG:

    from instagram import instagram_api

    @app.get("/test-message")
    async def test_message():

        recipient_id = "USER_ID_HERE"

        response = instagram_api.send_message(
            recipient_id,
            "Hello 👋 Bot test successful."
        )

        return response