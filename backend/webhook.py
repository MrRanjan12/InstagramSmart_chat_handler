import json
from fastapi import APIRouter, Request, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse

from backend.config import config
from backend.instagram import instagram_api
from backend.ai_agent import ai_agent
from backend.database import get_db_context
from backend.services.conversation_service import conversation_service
from backend.services.message_service import message_service
from backend.services.memory_service import memory_service
from backend.services.escalation.service import escalation_service
from backend.constants import RANJAN, ASTRA

router = APIRouter()

# Store processed message IDs to prevent duplicates
PROCESSED_MESSAGE_IDS = set()

# Store IDs of messages sent by the bot so we don't treat our own echoes as human replies
BOT_SENT_MESSAGE_IDS = set()


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


def build_media_prompt(
    attachment_type: str,
    user_text: str,
    media_url: str = None,
    media_id: str = None,
    title: str = None
) -> str:
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

Someone shared an Instagram reel or attachment with you.

Reel title:
{title or "Shared content"}

User caption:
{user_text or "No caption"}

Your task:
* Understand what the reel or attachment is probably about from the title.
* Reply like a real Instagram DM conversation.
* Don't describe the reel.
* Don't say "I watched the reel".
* Don't say "I cannot see the reel".
* Respond naturally as if a friend shared it with you.
* Keep it under 1-2 sentences unless needed.

Examples:
If reel is about a temple: "Achha lag raha hai yaar 🙏"
If reel is funny: "😂 ye mast tha"
If reel is motivational: "Bilkul sahi baat hai 💯"

Now generate only the reply.
"""


def process_human_echo_message(
    recipient_id: str,
    echo_text: str,
    message_id: str
):
    """
    Handles messages sent manually by Ranjan / Page Admin from the Instagram app.
    Saves them to Neon DB and maintains Human (RANJAN) mode so AI won't interfere.
    Also supports '#astra' or '#bot' command to re-enable AI.
    """
    clean_text = (echo_text or "").strip()
    if not clean_text:
        return

    try:
        with get_db_context() as db:
            user = conversation_service.get_or_create_user(
                db=db,
                instagram_id=recipient_id
            )

            conversation = conversation_service.get_or_create_conversation(
                db=db,
                user_id=user.id
            )

            # Check if Ranjan sent a reset command to reactivate AI
            if clean_text.lower() in ("#astra", "#bot", "/astra", "/bot", "!astra", "!bot", "bot on"):
                escalation_service.reset_to_ai(db, recipient_id)
                print(f"[ECHO] Human issued AI reset command '{clean_text}'. Switched user {recipient_id} back to ASTRA mode.")
                return

            # Save the human's manual reply in the database as assistant role
            message_service.save_ai_message(
                db=db,
                conversation_id=conversation.id,
                text=clean_text
            )

            # Ensure user is in RANJAN (Human) mode since owner is manually chatting
            if user.current_node != RANJAN:
                escalation_service.switch_user_mode(db, recipient_id, RANJAN)
                print(f"[ECHO] Human takeover confirmed for user {recipient_id}. Switched to RANJAN mode.")

            print(f"[ECHO] Saved manual reply from Ranjan to Neon DB for user {recipient_id}: {clean_text}")

    except Exception as e:
        print(f"[ECHO] Error saving human echo message to Neon: {e}")


def process_message_async(
    sender_id: str,
    user_display_text: str,
    prompt_for_ai: str,
    message_id: str
):
    """
    Background worker that runs asynchronously with automatic retry for Neon DB.
    1. Saves incoming message (Text or Reel/Media) to Neon DB.
    2. Evaluates Human Escalation and Mode Routing.
    3. If in AI mode, generates context-aware reply using conversation history.
    4. Saves AI reply to Neon DB and sends Instagram DM.
    """
    try:
        with get_db_context() as db:
            # 1. Concurrency-safe user & conversation retrieval
            user = conversation_service.get_or_create_user(
                db=db,
                instagram_id=sender_id
            )

            conversation = conversation_service.get_or_create_conversation(
                db=db,
                user_id=user.id
            )

            # 2. Persist the user's incoming message in Neon DB immediately
            message_service.save_user_message(
                db=db,
                conversation_id=conversation.id,
                text=user_display_text
            )
            print(f"[DATABASE] Stored user message in Neon DB (Conv {conversation.id}): {user_display_text[:60]}")

            # 3. Evaluate escalation & mode routing
            evaluation = escalation_service.evaluate_and_route(
                db=db,
                user=user,
                conversation_id=conversation.id,
                current_message=user_display_text
            )

            # If user was escalated to human in this turn and handoff message was generated:
            if evaluation.get("was_escalated") and evaluation.get("handoff_sent"):
                # Track handoff message ID if available
                print(f"[ESCALATION] Handoff message sent and mode switched to RANJAN for user {sender_id}.")

            if not evaluation["should_ai_reply"]:
                print(
                    f"[ROUTER] Skipping AI response for user {sender_id}. "
                    f"Mode: {evaluation.get('current_mode')}, Reason: {evaluation.get('reason')}"
                )
                return

            # 4. Fetch recent conversation history for LLM context
            history = memory_service.get_recent_messages(
                db=db,
                conversation_id=conversation.id,
                limit=getattr(config, "MAX_CONTEXT_MESSAGES", 10)
            )

            # Build messages list: all previous turns + current prompt
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in history[:-1]
            ]
            messages.append({"role": "user", "content": prompt_for_ai})

            # 5. Generate AI reply
            reply = ai_agent.generate_reply(messages)
            if not reply or not reply.strip():
                reply = "Hey! Bol bhai kya haal chal? 😄"

            print(f"[AI] Generated reply for {sender_id}: {reply}")

            # 6. Save AI reply to Neon DB
            message_service.save_ai_message(
                db=db,
                conversation_id=conversation.id,
                text=reply
            )
            print(f"[DATABASE] Stored AI reply in Neon DB (Conv {conversation.id}): {reply[:60]}")

            # 7. Send message via Instagram API
            resp = instagram_api.send_message(
                sender_id,
                reply
            )

            if isinstance(resp, dict) and "message_id" in resp:
                BOT_SENT_MESSAGE_IDS.add(resp["message_id"])

    except Exception as e:
        print(f"[ERROR] Failed to process incoming message for {sender_id}: {e}")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Meta Instagram Webhook Endpoint.
    Responds immediately with 200 OK (< 10ms) to satisfy Meta's 5s timeout.
    All DB queries and AI logic are scheduled in background tasks.
    """
    body = await request.json()

    if config.DEBUG:
        print("\nFULL WEBHOOK PAYLOAD")
        print("=" * 60)
        print(json.dumps(body, indent=2))
        print("=" * 60)

    try:
        entries = body.get("entry", [])

        for entry in entries:
            messaging_events = entry.get("messaging", [])

            for messaging in messaging_events:
                sender_id = messaging.get("sender", {}).get("id")
                recipient_id = messaging.get("recipient", {}).get("id")
                message_data = messaging.get("message", {})

                if not message_data:
                    continue

                message_id = message_data.get("mid")
                if not message_id:
                    continue

                # Handle Echo Messages (Sent from our bot or manually by Ranjan on Instagram)
                if message_data.get("is_echo"):
                    # If this message was sent by our bot, ignore it (already saved when sent)
                    if instagram_api.is_bot_message(message_id) or message_id in BOT_SENT_MESSAGE_IDS:
                        BOT_SENT_MESSAGE_IDS.discard(message_id)
                        continue

                    # Message sent manually by Ranjan on Instagram app
                    echo_text = message_data.get("text", "")
                    if echo_text and recipient_id:
                        background_tasks.add_task(
                            process_human_echo_message,
                            recipient_id,
                            echo_text,
                            message_id
                        )
                    continue

                if not sender_id:
                    continue

                # Duplicate protection
                if message_id in PROCESSED_MESSAGE_IDS:
                    print(f"Duplicate skipped: {message_id}")
                    continue

                PROCESSED_MESSAGE_IDS.add(message_id)
                if len(PROCESSED_MESSAGE_IDS) > 2000:
                    PROCESSED_MESSAGE_IDS.clear()

                # -----------------------------
                # CASE 1: TEXT MESSAGE
                # -----------------------------
                if "text" in message_data:
                    message_text = message_data.get("text", "").strip()
                    if message_text:
                        print(f"TEXT MESSAGE: {message_text}")
                        background_tasks.add_task(
                            process_message_async,
                            sender_id,
                            message_text,
                            message_text,
                            message_id
                        )
                        continue

                # -----------------------------
                # CASE 2: MEDIA / REEL ATTACHMENTS
                # -----------------------------
                attachments = message_data.get("attachments", [])
                if not attachments:
                    continue

                attachment = attachments[0]
                attachment_type = attachment.get("type", "unknown")
                payload = attachment.get("payload", {})

                title = payload.get("title", "")
                media_id = payload.get("id") or payload.get("media_id")
                media_url = payload.get("url") or payload.get("link") or payload.get("permalink")
                user_text = message_data.get("text", "").strip()

                # Build clean display text for database
                if title:
                    user_display = f"[Shared Reel: {title}] {user_text}".strip()
                elif attachment_type != "unknown":
                    user_display = f"[{attachment_type.capitalize()} Attachment] {user_text}".strip()
                else:
                    user_display = f"[Attachment Shared] {user_text}".strip()

                prompt = build_media_prompt(
                    attachment_type=attachment_type,
                    user_text=user_text,
                    media_url=media_url,
                    media_id=media_id,
                    title=title
                )

                print(f"MEDIA ATTACHMENT: {user_display}")
                background_tasks.add_task(
                    process_message_async,
                    sender_id,
                    user_display,
                    prompt,
                    message_id
                )

    except Exception as e:
        print("Webhook error:", str(e))

    # Always return HTTP 200 immediately to Meta
    return {
        "status": "received"
    }
