import yt_dlp
import sys
import os
import time
import json
import pathlib

def resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def sanitize_input(input_str):
    return input_str.strip('"')

def download_media(request_json_path):
    print(f"📂 Loading request JSON: {request_json_path}")
    try:
        with open(request_json_path, "r", encoding="utf-8") as f:
            req = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        return

    url = req.get("url")
    mode = req.get("format")
    name = req.get("file_name", "output")
    download_dir = os.path.abspath(req.get("download_dir", "download"))
    os.makedirs(download_dir, exist_ok=True)

    print(f"🌐 URL: {url}")
    print(f"🎯 Mode: {mode}")
    print(f"📂 Download dir: {download_dir}")
    print(f"📄 File name: {name}")

    cookies = None
    if "youtube.com" in url or "youtu.be" in url:
        cookies = resource_path("cookies/youtube_cookies.txt")
    elif "nicovideo.jp" in url:
        cookies = resource_path("cookies/niconico_cookies.txt")

    def progress(d):
        print(f"🔹 Progress: {d}")

    common_opts = {
        'outtmpl': os.path.join(download_dir, name),
        'quiet': False,
        'retries': 3,
        'fragment_retries': 3,
        'progress_hooks': [progress]
    }
    if cookies:
        common_opts['cookiefile'] = cookies

    try:
        if mode == "audio":
            ydl_opts = {
                **common_opts,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        elif mode == "video":
            ydl_opts = {
                **common_opts,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            }
        else:
            print(f"❌ Unsupported mode: {mode}")
            return

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"✅ Download completed for {name}")
    except Exception as e:
        print(f"❌ Download failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python download.py <request_json_path>")

    download_media(sys.argv[1])
