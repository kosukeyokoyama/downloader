import os
import time
import json
import subprocess
from ftplib import FTP
import re
import urllib.parse
from email.mime.text import MIMEText
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import pathlib

# ---- 環境変数から Secrets を読み込む ----
FTP_HOST = os.environ["FTP_HOST"]
FTP_USER = os.environ["FTP_USER"]
FTP_PASS = os.environ["FTP_PASS"]

CLIENT_SECRET_CONTENT = os.environ["CLIENT_SECRET"]
CLIENT_SECRET1_CONTENT = os.environ["CLIENT_SECRET1"]

TOKEN_PATH = "token.json"
TOKEN1_PATH = "token1.json"

LOCAL_REQUEST_DIR = "upload_requests"
DOWNLOAD_DIR = "download"

id = ""
password = ""
to = ""
ID = ""

SCOPES_GMAIL = ['https://www.googleapis.com/auth/gmail.send']
SCOPES_DRIVE = ['https://www.googleapis.com/auth/drive.file']

# ---- Gmail 認証 ----
def gmail_authenticate():
    # client_secret.json を Secrets から生成
    with open("client_secret.json", "w", encoding="utf-8") as f:
        f.write(CLIENT_SECRET_CONTENT)

    creds = None
    if os.path.exists(TOKEN1_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN1_PATH, SCOPES_GMAIL)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES_GMAIL)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN1_PATH, "w") as f:
            f.write(creds.to_json())
    return creds

def create_message(to, subject, body):
    message = MIMEText(body, 'plain', 'utf-8')
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_message(service, user_id, message):
    sent_message = service.users().messages().send(userId=user_id, body=message).execute()
    print(f"Message sent. ID: {sent_message['id']}")

def send_gmail_notification(to_addr, subject, body):
    creds = gmail_authenticate()
    service = build('gmail', 'v1', credentials=creds)
    message = create_message(to_addr, subject, body)
    send_message(service, 'me', message)

# ---- 通知 ----
def tuuti(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("notify_method") != "gmail":
        print("ℹ️ 通知は無効化されています。スキップします。")
        os.remove(file_path)
        return

    global id, password, to
    to_addr = to
    subject = "✅ ダウンロード完了"
    file = f"{data['file_name']}.{data['format']}"
    file_encoded = urllib.parse.quote(file)

    body = (
        f"{data['file_name']} が選択肢に追加されました\n"
        f"ダウンロードは以下URLからできます\n"
        f"https://kosukedownload.kesug.com/download.php?id={id}&pass={password}&download_file={file_encoded}\n\n"
        f"サイトのアクセスリンク: https://kosukedownload.kesug.com/index.php?id={id}&pass={password}"
        f"\n何か問題があった場合は返信してください"
    )
    send_gmail_notification(to_addr, subject, body)
    print("✅ Gmail通知送信完了")
    os.remove(file_path)

# ---- FTP ----
def ftp_connect(retries=5, delay=5):
    for i in range(retries):
        try:
            ftp = FTP()
            ftp.connect(FTP_HOST, timeout=10)
            ftp.login(FTP_USER, FTP_PASS)
            print("FTP接続成功")
            return ftp
        except Exception as e:
            print(f"[{i+1}/{retries}] FTP接続失敗: {e}")
            time.sleep(delay)
    raise ConnectionError("FTP接続に失敗しました（リトライ上限）")

def list_ftp_files(ftp, path):
    files = []
    ftp.cwd(path)
    ftp.retrlines('NLST', files.append)
    return files

def download_ftp_file(ftp, ftp_path, local_path):
    with open(local_path, 'wb') as f:
        ftp.retrbinary(f"RETR {ftp_path}", f.write)

def remove_ftp_file(ftp, ftp_path):
    ftp.delete(ftp_path)

def upload_ftp_file(ftp, local_path, ftp_path, local_json):
    with open(local_path, 'rb') as f:
        ftp.storbinary(f"STOR " + ftp_path, f)
        tuuti(local_json)
    print(f"Uploaded {local_path} to {ftp_path}")

# ---- ローカルリクエスト処理 ----
def process_local_requests():
    for file_name in os.listdir(LOCAL_REQUEST_DIR):
        if not file_name.endswith('.json'):
            continue
        local_file = os.path.join(LOCAL_REQUEST_DIR, file_name)
        try:
            with open(local_file, 'r', encoding='utf-8') as f:
                request = json.load(f)
        except Exception as e:
            print(f"Failed to parse local JSON {file_name}: {e}")
            os.remove(local_file)
            continue

        folder_path = DOWNLOAD_DIR
        exe_to_run = "python3"
        script_path = "./scripts/download.py"
        url = request.get('url')
        if not isinstance(url, str):
            print(f"Invalid URL type in request: {type(url)}")
            os.remove(local_file)
            continue
        url_encoded = urllib.parse.quote(url, safe=":/?&=")

        file_name_clean = re.sub(r'[<>:"/\\|?*]', '', request['file_name'])
        global ID, id, to, password
        ID = request['user_id']
        id = ID
        password = request['password']
        to = request['gmail_address']
        mode = {'mp3': 'audio', 'mp4': 'video'}.get(request['format'])
        if mode is None or file_name_clean == "":
            print(f"Unsupported format: {request['format']}")
            os.remove(local_file)
            continue

        command = [
            exe_to_run,
            script_path,
            url_encoded,
            folder_path,
            file_name_clean,
            mode,
            local_file
        ]
        print(f"Running command: {' '.join(command)}")
        subprocess.run(command, shell=True)

# ---- メインループ ----
def main_loop():
    os.makedirs(LOCAL_REQUEST_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    
    try:
           # ダウンロードディレクトリのクリア
        for file in pathlib.Path(DOWNLOAD_DIR).iterdir():
            if file.is_file():
                file.unlink()
    except Exception as e:
        print(f"Error cleaning download dir: {e}")

    process_local_requests()
    time.sleep(0.1)

if __name__ == "__main__":
    main_loop()
