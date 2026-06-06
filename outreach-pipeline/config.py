import os
import sys
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME")

def validate():
    """Abort early if any required key is missing."""
    missing = [k for k, v in {
        "APOLLO_API_KEY": APOLLO_API_KEY,
        "HUNTER_API_KEY": HUNTER_API_KEY,
        "BREVO_API_KEY": BREVO_API_KEY,
        "SENDER_EMAIL": SENDER_EMAIL,
        "SENDER_NAME": SENDER_NAME,
    }.items() if not v]

    if missing:
        print(f"[ERROR] Missing required env vars: {', '.join(missing)}")
        print("        Copy .env.example to .env and fill in your keys.")
        sys.exit(1)
