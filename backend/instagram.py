import requests
from config import config


class InstagramAPI:
    def __init__(self):
        self.access_token = config.INSTAGRAM_ACCESS_TOKEN

        self.base_url = "https://graph.instagram.com/v25.0"

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
                json=payload
            )

            data = response.json()

            print("Instagram API Response:", data)

            return data

        except Exception as e:
            print("Instagram send error:", str(e))
            return {"error": str(e)}


instagram_api = InstagramAPI()