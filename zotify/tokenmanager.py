import base64
import requests
import time
from zotify.zotify import Zotify

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

class SpotifyTokenManager:
    def __init__(self):
        self.client_id = Zotify.CONFIG.get_client_id()
        self.client_secret = Zotify.CONFIG.get_client_secret()
        self.access_token = None
        self.expires_at = 0

    def get_token(self):
        if self.access_token and time.time() < self.expires_at:
            return self.access_token

        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        response = requests.post(
            SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
        )

        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.expires_at = time.time() + data["expires_in"] - 30
        return self.access_token
