# zoom_utils.py
import jwt
import time
from django.conf import settings
import requests

class ZoomAPI:
    def __init__(self):
        self.api_key = settings.ZOOM_API_KEY
        self.api_secret = settings.ZOOM_API_SECRET
        self.base_url = settings.ZOOM_API_BASE_URL
        self.jwt_token = self.generate_jwt()

    def generate_jwt(self):
        """Generate a JWT token using Zoom API Key and Secret."""
        payload = {
            "iss": self.api_key,
            "exp": time.time() + 3600,  # Token valid for 1 hour
        }
        token = jwt.encode(payload, self.api_secret, algorithm="HS256")
        return token

    def create_meeting(self, host_email, topic, start_time, duration):
        """Create a Zoom meeting."""
        url = f"{self.base_url}/users/{host_email}/meetings"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time,  # ISO8601 format
            "duration": duration,  # in minutes
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def get_meeting(self, meeting_id):
        """Retrieve a specific meeting's details."""
        url = f"{self.base_url}/meetings/{meeting_id}"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
