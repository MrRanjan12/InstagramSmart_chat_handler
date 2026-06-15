
from fastapi import FastAPI

from config import config
from webhook import router as webhook_router

from database import Base
from database import engine

from models.user import User
Base.metadata.create_all(
    bind=engine
)

app = FastAPI(
    title="Instagram AI Assistant",
    version="1.0.0"
)

# Register webhook routes
app.include_router(webhook_router)


@app.on_event("startup")
async def startup_event():

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
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():

    return {
        "status": "healthy",
        "service": config.BOT_NAME,
        "version": "1.0.0"
    }


# Development-only testing endpoint
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
