import yt_dlp
import sys
import os
import time
import glob
if len(sys.argv) > 2:
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
def resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def sanitize_input(input_str):
    return input_str.strip('"')

def download_audio(url, output_dir, name, retries=5, sleep_sec=5):
    filename = os.path.join(output_dir, name)
    mp3_path = filename + '.mp3'
    url = sanitize_input(url)
    youtube_cookie = resource_path("cookies/youtube_cookies.txt")
    nico_cookie = resource_path("cookies/niconico_cookies.txt")

    site_specific_opts = {}
    if "youtube.com" in url or "youtu.be" in url:
        site_specific_opts['cookiefile'] = youtube_cookie
    elif "nicovideo.jp" in url:
        site_specific_opts['cookiefile'] = nico_cookie

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': False,
        'socket_timeout': 180,
        'retries': retries,
        'fragment_retries': retries,
        **site_specific_opts
    }

    for attempt in range(retries):
        try:
            print(f"Audio: Attempt {attempt + 1} of {retries}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if os.path.exists(mp3_path):
                now = time.time()
                os.utime(mp3_path, (now, now))
                print(f"Timestamps updated: {mp3_path}")
            else:
                print(f"Warning: Expected file not found: {mp3_path}")
            print(f"Audio downloaded and saved as {name}.mp3")
            return True
        except Exception as e:
            print(f"Audio Error: {e}")
            if attempt < retries - 1:
                time.sleep(sleep_sec)
            else:
                print("Audio download failed.")
                return False

def download_video(url, output_dir, name, retries=5, sleep_sec=5):
    filename = os.path.join(output_dir, name)
    url = sanitize_input(url)
    youtube_cookie = resource_path("cookies/youtube_cookies.txt")
    nico_cookie = resource_path("cookies/niconico_cookies.txt")

    site_specific_opts = {}
    if "youtube.com" in url or "youtu.be" in url:
        site_specific_opts['cookiefile'] = youtube_cookie
    elif "nicovideo.jp" in url:
        site_specific_opts['cookiefile'] = nico_cookie

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': filename,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': False,
        'socket_timeout': 180,
        'retries': retries,
        'fragment_retries': retries,
        **site_specific_opts
    }

    for attempt in range(retries):
        try:
            print(f"Video: Attempt {attempt + 1} of {retries}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            matched_files = glob.glob(filename + '.mp4')
            if matched_files:
                target_file = matched_files[0]
                now = time.time()
                os.utime(target_file, (now, now))
                print(f"Timestamps updated: {target_file}")
                print(f"Video downloaded and saved as {name}.mp4")
                return True
            else:
                print(f"Warning: File not found for pattern: {filename}.mp4")
                return False
        except Exception as e:
            print(f"Video Error: {e}")
            if attempt < retries - 1:
                time.sleep(sleep_sec)
            else:
                print("Video download failed.")
                return False

if __name__ == '__main__':
    if len(sys.argv) < 6:
        sys.exit("Usage: python download.py <URL> <Download Directory> <Name> <mode: audio|video> <local_json>")

    url = sys.argv[1]
    download_dir = sys.argv[2]
    name = sys.argv[3]
    mode = sys.argv[4].lower()
    local_json = sys.argv[5]

    os.makedirs(download_dir, exist_ok=True)

    if mode == 'audio':
        download_audio(url, download_dir, name)
    elif mode == 'video':
        download_video(url, download_dir, name)
    else:
        sys.exit("Mode must be 'audio' or 'video'")
