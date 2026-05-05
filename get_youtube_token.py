"""
get_youtube_token.py
RUN THIS ONCE ON YOUR LOCAL PC — NOT ON GITHUB ACTIONS.
Gets the YouTube OAuth refresh token you need for each channel.

Steps:
  1. Go to Google Cloud Console → dopamine-loop project
  2. APIs & Services → Credentials → Create OAuth 2.0 Client ID
  3. Application type: Desktop App
  4. Download the JSON → save as client_secret.json in this folder
  5. Run: python get_youtube_token.py
  6. Browser opens → log in with the YouTube channel's Google account
  7. Copy the printed refresh token → paste into GitHub secret

Run once per YouTube channel (5 times total for 5 channels).
Name your secrets: YOUTUBE_REFRESH_TOKEN_CH1, _CH2, etc.
"""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    if not os.path.exists("client_secret.json"):
        print("ERROR: client_secret.json not found.")
        print("Download it from Google Cloud Console → APIs & Services → Credentials")
        return

    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "="*60)
    print("YOUR REFRESH TOKEN (copy this to GitHub secrets):")
    print("="*60)
    print(creds.refresh_token)
    print("="*60)
    print(f"\nClient ID:     {creds.client_id}")
    print(f"Client Secret: {creds.client_secret}")
    print("\nAdd these to GitHub Actions secrets:")
    print("  YOUTUBE_REFRESH_TOKEN_CH1 = <refresh token above>")
    print("  YOUTUBE_CLIENT_ID         = <client id above>")
    print("  YOUTUBE_CLIENT_SECRET     = <client secret above>")


if __name__ == "__main__":
    main()
