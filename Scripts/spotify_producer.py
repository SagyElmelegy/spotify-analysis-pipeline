# Reads what you are playing on Spotify and sends it to Kafka.
# Run locally or inside the spotify_producer Docker container.

import json
import logging
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from kafka import KafkaProducer

# Show logs right away in Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger(__name__)

# Load settings from the .env file in the project root
env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "spotify_topic")
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
WAIT_SECONDS = int(os.getenv("SPOTIFY_POLL_INTERVAL_SECONDS", "30"))


def get_access_token():
    """Get a short-lived Spotify access token using the refresh token in .env."""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")

    if not REFRESH_TOKEN:
        raise ValueError("Set SPOTIFY_REFRESH_TOKEN in .env (run get_spotify_refresh_token.py first)")

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def main():
    log.info("Connecting to Kafka at %s", KAFKA_SERVERS)

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVERS,
        value_serializer=lambda record: json.dumps(record).encode("utf-8"),
    )

    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    log.info("Producer started. Topic: %s", KAFKA_TOPIC)

    while True:
        try:
            response = requests.get(
                "https://api.spotify.com/v1/me/player/currently-playing",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json() or {
                    "status": "paused",
                    "timestamp": int(time.time() * 1000),
                }
                producer.send(KAFKA_TOPIC, value=data)
                producer.flush()
                song = data.get("item", {}).get("name", "Paused")
                log.info("Produced: %s", song)

            elif response.status_code == 204:
                # Nothing is playing right now
                data = {"status": "nothing_playing", "timestamp": int(time.time() * 1000)}
                producer.send(KAFKA_TOPIC, value=data)
                producer.flush()
                log.info("Produced: nothing playing")

            elif response.status_code == 401:
                # Token expired — get a new one
                access_token = get_access_token()
                headers["Authorization"] = f"Bearer {access_token}"
                log.info("Refreshed Spotify token")

            else:
                log.warning("Spotify API returned %s: %s", response.status_code, response.text)

        except Exception as error:
            log.error("Error: %s", error)

        time.sleep(WAIT_SECONDS)


if __name__ == "__main__":
    main()
