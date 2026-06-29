# Reads Spotify messages from Kafka and saves each one as a JSON file in S3.
# Run locally or inside the spotify_consumer Docker container.

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3
from dotenv import load_dotenv
from kafka import KafkaConsumer
from kafka.serializer import Deserializer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger(__name__)

env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "spotify_topic")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "spotify-bronze-data-bucket")


class JsonDeserializer(Deserializer):
    # kafka-python 3.x wants a proper deserializer class instead of a lambda

    def deserialize(self, topic, headers, data):
        if data is None:
            return None
        return json.loads(data.decode("utf-8"))


def main():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        region_name=AWS_REGION,
    )

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=JsonDeserializer(),
    )

    log.info("Consumer started. Kafka: %s, topic: %s", KAFKA_SERVERS, KAFKA_TOPIC)

    for message in consumer:
        data = message.value
        now = datetime.now(timezone.utc)

        # Example path: bronze/year=2026/month=6/day=29/spotify_1234567890.json
        s3_key = (
            f"bronze/year={now.year}/month={now.month}/day={now.day}/"
            f"spotify_{int(now.timestamp())}.json"
        )

        try:
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=json.dumps(data),
            )
            log.info("Uploaded to S3: s3://%s/%s", BUCKET_NAME, s3_key)
        except Exception as error:
            log.error("S3 upload failed: %s", error)


if __name__ == "__main__":
    main()
