from backend.services.memory_service import memory_service
from fastapi import APIRouter, Request, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse

from backend.config import config
from backend.instagram import instagram_api
from backend.ai_agent import ai_agent

from backend.database import get_db
from backend.services.conversation_service import conversation_service
from backend.services.message_service import message_service

import json

router = APIRouter()

# Store processed message IDs
PROCESSED_MESSAGE_IDS = set()


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    print("Webhook verification request received")

    if (
        hub_mode == "subscribe"
        and hub_verify_token == config.INSTAGRAM_VERIFY_TOKEN
    ):
        print("Webhook verified successfully")

        return PlainTextResponse(
            content=hub_challenge,
            status_code=200
        )

    return PlainTextResponse(
        content="Verification failed",
        status_code=403
    )

def save_message_to_database(
    sender_id: str,
    message_text: str
):
    db = next(get_db())

    try:

        user = conversation_service.get_or_create_user(
            db=db,
            instagram_id=sender_id
        )

        conversation = (
            conversation_service.get_or_create_conversation(
                db=db,
                user_id=user.id
            )
        )

        message_service.save_user_message(
            db=db,
            conversation_id=conversation.id,
            text=message_text
        )

    finally:
        db.close()

def process_message_async(
    sender_id: str,
    prompt: str,
    message_id: str
):
    db = next(get_db())

    try:

        user = conversation_service.get_or_create_user(
            db=db,
            instagram_id=sender_id
        )

        conversation = conversation_service.get_or_create_conversation(
            db=db,
            user_id=user.id
        )

        history = memory_service.get_recent_messages(
            db=db,
            conversation_id=conversation.id
        )

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

        reply = ai_agent.generate_reply(messages)

        print("AI Reply:", reply)

        message_service.save_ai_message(
            db=db,
            conversation_id=conversation.id,
            text=reply
        )

        instagram_api.send_message(
            sender_id,
            reply
        )

    except Exception as e:

        print(
            "Error processing async task:",
            str(e)
        )

    finally:
        db.close()

def build_media_prompt(
    attachment_type: str,
    user_text: str,
    media_url: str = None,
    media_id: str = None,
    title: str = None
):
    return f"""
EVENT_TYPE: {attachment_type}

REEL_TITLE:
{title or "No title"}

REEL_URL:
{media_url or "No URL"}

MEDIA_ID:
{media_id or "No Media ID"}

USER_CAPTION:
{user_text or "No Caption"}

You are Ranjan.

Someone shared an Instagram reel with you.

Reel title:
{title}

User caption:
{user_text or "No caption"}

Your task:

* Understand what the reel is probably about from the title.
* Reply like a real Instagram DM conversation.
* Don't describe the reel.
* Don't say "I watched the reel".
* Don't say "I cannot see the reel".
* Respond naturally as if a friend shared it with you.
* Keep it under 1 sentence unless needed.

Examples:

If reel is about a temple:
"Achha lag raha hai yaar 🙏"

If reel is funny:
"😂 ye mast tha"

If reel is motivational:
"Bilkul sahi baat hai 💯"

Now generate only the reply.

"""



@router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    body = await request.json()

    print("\nFULL WEBHOOK PAYLOAD")
    print("=" * 100)

    print(
        json.dumps(
            body,
            indent=2
        )
    )

    print("=" * 100)

    try:

        entries = body.get("entry", [])

        for entry in entries:

            messaging_events = entry.get(
                "messaging",
                []
            )

            for messaging in messaging_events:

                sender_id = (
                    messaging
                    .get("sender", {})
                    .get("id")
                )

                if not sender_id:
                    continue

                message_data = messaging.get(
                    "message",
                    {}
                )

                # Ignore messages sent by bot
                if message_data.get("is_echo"):

                    print(
                        "Skipping echo message"
                    )

                    continue

                message_id = message_data.get(
                    "mid"
                )

                if not message_id:

                    print(
                        "Missing message ID"
                    )

                    continue

                # Duplicate protection
                if (
                    message_id
                    in PROCESSED_MESSAGE_IDS
                ):

                    print(
                        f"Duplicate skipped: {message_id}"
                    )

                    continue

                PROCESSED_MESSAGE_IDS.add(
                    message_id
                )

                # Prevent memory growth
                if (
                    len(PROCESSED_MESSAGE_IDS)
                    > 1000
                ):
                    PROCESSED_MESSAGE_IDS.clear()

                # -----------------------------
                # TEXT MESSAGE
                # -----------------------------

                if "text" in message_data:

                    message_text = (
                        message_data["text"]
                    )

                    print(
                        f"TEXT MESSAGE: {message_text}"
                    )
                    
                    save_message_to_database(
                        sender_id,
                        message_text
                    )

                    background_tasks.add_task(
                        process_message_async,
                        sender_id,
                        message_text,
                        message_id
                    )

                    continue

                # -----------------------------
                # MEDIA ATTACHMENTS
                # -----------------------------

                attachments = message_data.get(
                    "attachments",
                    []
                )

                if not attachments:

                    print(
                        "No attachments found"
                    )

                    continue

                attachment = attachments[0]

                attachment_type = attachment.get(
                    "type",
                    "unknown"
                )

                payload = attachment.get(
                    "payload",
                    {}
                )
                
                # Reel metadata
                title = payload.get(
                    "title",
                    ""
                )

                reel_video_id = payload.get(
                    "reel_video_id",
                    ""
                )

                media_id = (
                    payload.get("id")
                    or payload.get("media_id")
                )

                media_url = (
                    payload.get("url")
                    or payload.get("link")
                    or payload.get("permalink")
                )

                user_text = message_data.get(
                    "text",
                    ""
                )

                print("\nATTACHMENT DEBUG")
                print("-" * 50)

                print(
                    json.dumps(
                        attachment,
                        indent=2
                    )
                )

                print(
                    f"Attachment Type: {attachment_type}"
                )

                print(
                    f"Media ID: {media_id}"
                )

                print(
                    f"Media URL: {media_url}"
                )

                print(
                    f"User Caption: {user_text}"
                )

                print("-" * 50)

                prompt = build_media_prompt(
                    attachment_type=attachment_type,
                    user_text=user_text,
                    media_url=media_url,
                    media_id=media_id,
                    title=title
                )

                background_tasks.add_task(
                    process_message_async,
                    sender_id,
                    prompt,
                    message_id
                )

    except Exception as e:

        print(
            "Webhook error:",
            str(e)
        )

    return {
        "status": "received"
    }

