#!/usr/bin/env python3
"""
upload_youtube.py
Upload video ke YouTube Shorts menggunakan OAuth2 Refresh Token.
Refresh token tidak pernah expired selama dipakai minimal sekali setiap 6 bulan.
"""

import os
import sys
import json
import argparse
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


# ─── Ambil credentials dari environment variable (GitHub Secrets) ───────────

CLIENT_ID     = os.environ.get("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

TOKEN_URI = "https://oauth2.googleapis.com/token"


def get_authenticated_service():
    """Buat credentials dari refresh token dan return YouTube service."""

    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        print("❌ ERROR: Environment variable tidak lengkap!")
        print("   Pastikan secrets berikut sudah diset di GitHub:")
        print("   - YOUTUBE_CLIENT_ID")
        print("   - YOUTUBE_CLIENT_SECRET")
        print("   - YOUTUBE_REFRESH_TOKEN")
        sys.exit(1)

    credentials = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )

    # Refresh untuk dapat access token baru otomatis
    credentials.refresh(Request())
    print("✅ Token berhasil di-refresh!")

    youtube = build("youtube", "v3", credentials=credentials)
    return youtube


def upload_video(youtube, file_path, title, description, tags):
    """Upload video ke YouTube sebagai Shorts."""

    if not os.path.exists(file_path):
        print(f"❌ ERROR: File tidak ditemukan: {file_path}")
        sys.exit(1)

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"📁 File  : {file_path}")
    print(f"📦 Size  : {file_size_mb:.2f} MB")
    print(f"📝 Title : {title}")

    # Pastikan ada #Shorts di deskripsi agar YouTube kenali sebagai Shorts
    if "#Shorts" not in description and "#shorts" not in description:
        description = description + "\n\n#Shorts"

    # Parse tags dari string "tag1,tag2,tag3"
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    if "shorts" not in [t.lower() for t in tag_list]:
        tag_list.append("shorts")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tag_list,
            "categoryId": "22",  # People & Blogs (umum untuk Shorts)
            "defaultLanguage": "id",
        },
        "status": {
            "privacyStatus": "public",   # public | private | unlisted
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }

    media = MediaFileUpload(
        file_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,  # 5MB per chunk
    )

    print("📤 Memulai upload ke YouTube...")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"   Upload progress: {progress}%")

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/shorts/{video_id}"

    print("")
    print("=" * 50)
    print("✅ UPLOAD BERHASIL!")
    print(f"🎬 Video ID  : {video_id}")
    print(f"🔗 URL       : {video_url}")
    print("=" * 50)

    # Tulis ke file untuk ditangkap GitHub Actions summary jika perlu
    with open("youtube_result.json", "w") as f:
        json.dump({
            "video_id": video_id,
            "url": video_url,
            "title": title,
        }, f, indent=2)

    # Set GitHub Actions output
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"youtube_url={video_url}\n")
            f.write(f"video_id={video_id}\n")

    return video_id


def main():
    parser = argparse.ArgumentParser(description="Upload video ke YouTube Shorts")
    parser.add_argument("--file",        required=True,  help="Path ke file .mp4")
    parser.add_argument("--title",       required=True,  help="Judul video")
    parser.add_argument("--description", default="",     help="Deskripsi video")
    parser.add_argument("--tags",        default="shorts", help="Tags pisah koma")
    args = parser.parse_args()

    print("🔐 Authenticating ke YouTube API...")
    youtube = get_authenticated_service()

    upload_video(
        youtube=youtube,
        file_path=args.file,
        title=args.title,
        description=args.description,
        tags=args.tags,
    )


if __name__ == "__main__":
    main()
