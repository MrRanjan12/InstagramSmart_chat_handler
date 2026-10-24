import requests
from backend.config import config


class InstagramAPI:
    def __init__(self):
        self.access_token = config.INSTAGRAM_ACCESS_TOKEN
        self.base_url = "https://graph.instagram.com/v25.0"
        self.sent_message_ids = set()

    def send_message(self, recipient_id: str, message_text: str):
        url = f"{self.base_url}/{config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/messages"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": message_text
            }
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )

            data = response.json()
            print("Instagram API Response:", data)

            if isinstance(data, dict):
                mid = data.get("message_id") or data.get("mid")
                if mid:
                    self.sent_message_ids.add(mid)
                    if len(self.sent_message_ids) > 2000:
                        self.sent_message_ids.clear()

            return data

        except Exception as e:
            print("Instagram send error:", str(e))
            return {"error": str(e)}

    def is_bot_message(self, message_id: str) -> bool:
        if not message_id:
            return False
        if message_id in self.sent_message_ids:
            self.sent_message_ids.discard(message_id)
            return True
        return False


instagram_api = InstagramAPI()