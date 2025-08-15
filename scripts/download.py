import yt_dlp
import sys
import os
import subprocess
import glob
import time

def resource_path(relative_path):
    """ GitHub Actions などでも相対パスで cookie 等を参照 """
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def sanitize_input(input_str):
    """ ダブルクオーテーションを除去 """
    return input_str.strip('"')

def download_audio(url, output_dir, name, retries=5, sleep_sec=5):
    filename = os.path.join(output_dir, name)
    mp3_path = filename + '.mp3'
    url = sanitize_input(url)
    youtube_cookie = resource_path("cookies/youtube_cookies.txt")
    nico_cookie = resource_path("cookies/niconico_cookies.txt")

# cookie 設定部分
    site_specific_opts = {}
    youtube_cookie_env = os.environ.get("YT_COOKIE_FILE")
    youtube_cookie_secret = os.environ.get("YT_COOKIE")  # GitHub Secrets の直接値
    nico_cookie = resource_path("cookies/niconico_cookies.txt")

    if "youtube.com" in url or "youtu.be" in url:
        if youtube_cookie_env and os.path.exists(youtube_cookie_env):
            site_specific_opts['cookiefile'] = youtube_cookie_env
            print(f"Using cookie file: {youtube_cookie_env}")
        elif youtube_cookie_secret:
            # YT_COOKIE が文字列なら一時ファイルに保存
            tmp_cookie_path = os.path.join(output_dir, "yt_cookie.txt")
            with open(tmp_cookie_path, "w", encoding="utf-8") as f:
                f.write(youtube_cookie_secret)
            site_specific_opts['cookiefile'] = tmp_cookie_path
            print("Using cookie from YT_COOKIE secret")
        else:
            print("No YouTube cookie provided — continuing without cookies.")

    elif "nicovideo.jp" in url and os.path.exists(nico_cookie):
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
        'quiet': True,
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
            # GitHub Actions ではローカル subprocess 呼び出しは不要
            # subprocess.run(["python3", "./scripts/audio.py", mp3_path])
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
# cookie 設定部分
    site_specific_opts = {}
    youtube_cookie_env = os.environ.get("YT_COOKIE_FILE")
    youtube_cookie_secret = os.environ.get("YT_COOKIE")  # GitHub Secrets の直接値
    nico_cookie = resource_path("cookies/niconico_cookies.txt")

    if "youtube.com" in url or "youtu.be" in url:
        if youtube_cookie_env and os.path.exists(youtube_cookie_env):
            site_specific_opts['cookiefile'] = youtube_cookie_env
            print(f"Using cookie file: {youtube_cookie_env}")
        elif youtube_cookie_secret:
            # YT_COOKIE が文字列なら一時ファイルに保存
            tmp_cookie_path = os.path.join(output_dir, "yt_cookie.txt")
            with open(tmp_cookie_path, "w", encoding="utf-8") as f:
                f.write(youtube_cookie_secret)
            site_specific_opts['cookiefile'] = tmp_cookie_path
            print("Using cookie from YT_COOKIE secret")
        else:
            print("No YouTube cookie provided — continuing without cookies.")

    elif "nicovideo.jp" in url and os.path.exists(nico_cookie):
        site_specific_opts['cookiefile'] = nico_cookie
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': filename,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
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
                # subprocess.run(["python3", "./scripts/audio.py", target_file])
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
        sys.exit("Usage: python download_media.py <URL> <Download Directory> <Name> <mode: audio|video> <local_json>")

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
