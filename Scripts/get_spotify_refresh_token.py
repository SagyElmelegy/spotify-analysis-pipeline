# One-time script to get a Spotify refresh token for the producer.
#
# 1. Add http://127.0.0.1:8888 as a Redirect URI in the Spotify Developer Dashboard
# 2. Run: python Scripts/get_spotify_refresh_token.py
# 3. Copy the refresh token into your .env file

import base64
import hashlib
import os
import secrets
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
from dotenv import load_dotenv

env_file = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_file)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
HOST = os.getenv("SPOTIFY_OAUTH_HOST", "127.0.0.1")
PORT = int(os.getenv("SPOTIFY_OAUTH_PORT", "8888"))
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", f"http://{HOST}:{PORT}")
SCOPES = "user-read-currently-playing"

# These get filled in when Spotify redirects back to our local server
authorization_code = None
authorization_error = None


def make_pkce_codes():
    """PKCE is required for Spotify login without a client secret in the browser."""
    verifier = secrets.token_urlsafe(64)[:128]
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("utf-8")).digest()
    ).decode("utf-8").rstrip("=")
    return verifier, challenge


class SpotifyCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global authorization_code, authorization_error

        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

        if "error" in query:
            authorization_error = query["error"][0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Login failed. You can close this tab.")
            return

        code = query.get("code", [None])[0]
        if not code:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code received from Spotify.")
            return

        authorization_code = code
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Success! Go back to the terminal.")

    def log_message(self, format, *args):
        pass  # keep the terminal output clean


def wait_for_spotify_login(server):
    while authorization_code is None and authorization_error is None:
        server.handle_request()


def main():
    if not CLIENT_ID:
        raise SystemExit("Add SPOTIFY_CLIENT_ID to .env first.")

    verifier, challenge = make_pkce_codes()

    login_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
        {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
        }
    )

    print("Add this Redirect URI in Spotify Developer Dashboard:")
    print(f"  {REDIRECT_URI}")
    print("Press Enter when done...")
    input()

    server = HTTPServer((HOST, PORT), SpotifyCallbackHandler)
    thread = threading.Thread(target=wait_for_spotify_login, args=(server,), daemon=True)
    thread.start()

    print(f"\nWaiting for login at {REDIRECT_URI}")
    print("Opening browser...\n")
    webbrowser.open(login_url)

    thread.join(timeout=300)
    server.server_close()

    if authorization_error:
        raise SystemExit(f"Spotify error: {authorization_error}")

    if not authorization_code:
        raise SystemExit("Timed out waiting for Spotify login.")

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "code_verifier": verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    if not response.ok:
        raise SystemExit(
            f"Token exchange failed ({response.status_code}): {response.text}\n"
            f"Make sure Redirect URI matches exactly: {REDIRECT_URI}"
        )

    refresh_token = response.json().get("refresh_token")
    if not refresh_token:
        raise SystemExit(f"No refresh token in response: {response.json()}")

    print("\nAdd these lines to your .env file:\n")
    print(f"SPOTIFY_REDIRECT_URI={REDIRECT_URI}")
    print(f"SPOTIFY_REFRESH_TOKEN={refresh_token}")


if __name__ == "__main__":
    main()
