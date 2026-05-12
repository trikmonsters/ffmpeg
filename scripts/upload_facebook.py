#!/usr/bin/env python3
"""
upload_facebook.py
Upload video ke Facebook Reels menggunakan Graph API.
Access token dikirim dari App Script (tidak disimpan di GitHub Secrets).

Flow upload Facebook Reels (Resumable Upload):
  1. Init upload session → dapat upload_url & video_id
  2. Upload binary video ke upload_url
  3. Publish video sebagai Reel ke Page
"""

import os
import sys
import json
import time
import argparse
import requests


GRAPH_API_VERSION = "v19.0"
GRAPH_BASE        = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def init_upload_session(page_id: str, access_token: str, file_size: int, title: str) -> dict:
    """Step 1: Inisialisasi sesi upload, dapat upload_url."""
    print("📋 Inisialisasi Facebook upload session...")

    url = f"{GRAPH_BASE}/{page_id}/video_reels"
    payload = {
        "upload_phase": "start",
        "access_token": access_token,
    }

    resp = requests.post(url, data=payload)
    data = resp.json()

    if "error" in data:
        print(f"❌ Gagal init session: {data['error'].get('message', data)}")
        sys.exit(1)

    video_id  = data.get("video_id")
    upload_url = data.get("upload_url")

    print(f"✅ Session OK — Video ID: {video_id}")
    return {"video_id": video_id, "upload_url": upload_url}


def upload_video_binary(upload_url: str, file_path: str, access_token: str) -> bool:
    """Step 2: Upload binary file ke upload_url."""
    file_size = os.path.getsize(file_path)
    print(f"📤 Uploading ke Facebook ({file_size / (1024*1024):.1f} MB)...")

    with open(file_path, "rb") as f:
        headers = {
            "Authorization": f"OAuth {access_token}",
            "offset":        "0",
            "file_size":     str(file_size),
        }
        resp = requests.post(upload_url, headers=headers, data=f)

    if resp.status_code not in [200, 201]:
        print(f"❌ Upload binary gagal: {resp.status_code} — {resp.text[:300]}")
        sys.exit(1)

    print("✅ Binary upload berhasil!")
    return True


def publish_reel(page_id: str, access_token: str, video_id: str, title: str, description: str, tags: str) -> dict:
    """Step 3: Publish video sebagai Reel."""
    print("📢 Publishing sebagai Facebook Reel...")

    # Gabungkan hashtags dari tags
    tag_list    = [t.strip() for t in tags.split(",") if t.strip()]
    hashtags    = " ".join([f"#{t}" if not t.startswith("#") else t for t in tag_list])
    full_desc   = f"{description}\n\n{hashtags}" if hashtags else description

    url = f"{GRAPH_BASE}/{page_id}/video_reels"
    payload = {
        "video_id":     video_id,
        "upload_phase": "finish",
        "access_token": access_token,
        "video_state":  "PUBLISHED",
        "description":  full_desc[:2200],  # max 2200 karakter Facebook
        "title":        title[:255],
    }

    resp = requests.post(url, data=payload)
    data = resp.json()

    if "error" in data:
        print(f"❌ Publish gagal: {data['error'].get('message', data)}")
        sys.exit(1)

    reel_url = f"https://www.facebook.com/reel/{video_id}"
    print(f"✅ Facebook Reel published!")
    print(f"   Video ID : {video_id}")
    print(f"   URL      : {reel_url}")

    return {"platform": "facebook", "video_id": video_id, "url": reel_url}


def main():
    parser = argparse.ArgumentParser(description="Upload video ke Facebook Reels")
    parser.add_argument("--file",         required=True,  help="Path file .mp4")
    parser.add_argument("--page-id",      required=True,  help="Facebook Page ID")
    parser.add_argument("--access-token", required=True,  help="Facebook Page Access Token")
    parser.add_argument("--title",        required=True,  help="Judul video")
    parser.add_argument("--description",  default="",     help="Deskripsi video")
    parser.add_argument("--tags",         default="",     help="Tags pisah koma")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ File tidak ditemukan: {args.file}")
        sys.exit(1)

    if not args.access_token or args.access_token.strip() == "":
        print("❌ Facebook access token kosong!")
        sys.exit(1)

    if not args.page_id or args.page_id.strip() == "":
        print("❌ Facebook page ID kosong!")
        sys.exit(1)

    file_size = os.path.getsize(args.file)

    # Step 1: Init session
    session = init_upload_session(args.page_id, args.access_token, file_size, args.title)

    # Step 2: Upload binary
    upload_video_binary(session["upload_url"], args.file, args.access_token)

    # Step 3: Publish
    result = publish_reel(
        args.page_id,
        args.access_token,
        session["video_id"],
        args.title,
        args.description,
        args.tags,
    )

    # Simpan/append hasil ke upload_results.json
    results = []
    if os.path.exists("upload_results.json"):
        with open("upload_results.json") as f:
            results = json.load(f)
    results.append(result)
    with open("upload_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # GitHub Actions output
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"facebook_url={result['url']}\n")
            f.write(f"facebook_video_id={result['video_id']}\n")


if __name__ == "__main__":
    main()
