# Quick test to check AWS credentials and that the bronze bucket exists.

import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

env_file = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_file)

bucket_name = os.getenv("S3_BUCKET_NAME", "spotify-bronze-data-bucket")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)


def main():
    try:
        response = s3.list_buckets()
        print("Connected to S3!")
        for bucket in response["Buckets"]:
            print(f" - {bucket['Name']}")

        found = any(b["Name"] == bucket_name for b in response["Buckets"])
        if found:
            print(f"\nBucket '{bucket_name}' exists.")
        else:
            print(f"\nBucket '{bucket_name}' was not found. Create it in AWS first.")

    except Exception as error:
        print(f"Error connecting to S3: {error}")
        print("\nCheck:")
        print("1. AWS_ACCESS_KEY and AWS_SECRET_KEY are in .env")
        print("2. The keys are correct")
        print("3. Your IAM user can access S3")


if __name__ == "__main__":
    main()
