"""One-time helper script to generate YouTube OAuth Refresh Token.
Run locally in your terminal:
python scripts/get_youtube_token.py
"""

import os
import sys
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    load_dotenv()
    print("=" * 60)
    print("YouTube Data API v3: Headless Refresh Token Generator")
    print("=" * 60)

    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")

    if not client_id or not client_secret:
        client_id = input("Enter your YouTube Client ID: ").strip()
        client_secret = input("Enter your YouTube Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Error: Both Client ID and Client Secret are required.")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    print("\nOpening browser for one-time Google Account authentication...")
    print("Sign in with the Google Account that owns your YouTube channel and grant permission.\n")

    credentials = flow.run_local_server(port=8080, access_type="offline", prompt="consent")

    refresh_token = credentials.refresh_token

    print("\n" + "=" * 60)
    print("SUCCESS! Generated Refresh Token:")
    print("=" * 60)
    print(f"YOUTUBE_REFRESH_TOKEN={refresh_token}")
    print("=" * 60)

    # Automatically save to .env
    env_path = Path(".env")
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("YOUTUBE_REFRESH_TOKEN="):
                new_lines.append(f"YOUTUBE_REFRESH_TOKEN={refresh_token}")
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f"YOUTUBE_REFRESH_TOKEN={refresh_token}")
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print("\n[OK] Automatically updated YOUTUBE_REFRESH_TOKEN in your local .env file!")

    print("\nFor GitHub Actions (cloud deployment):")
    print("Add this secret under your GitHub Repo Settings > Secrets and variables > Actions:")
    print(f"Name:  YOUTUBE_REFRESH_TOKEN")
    print(f"Value: {refresh_token}\n")


if __name__ == "__main__":
    main()
