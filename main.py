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
import ast

data = ""

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
    client_secret_data = {}
    try:
        # 環境変数の文字列をPython辞書として安全に評価する
        client_secret_data = ast.literal_eval(CLIENT_SECRET_CONTENT)
    except (ValueError, SyntaxError) as e:
        print(f"CLIENT_SECRET_CONTENT の解析に失敗しました。JSON形式を確認してください: {e}")
        return None
    
    with open("client_secret.json", "w", encoding="utf-8") as f:
        # 辞書を厳密なJSON形式でファイルに書き出す
        json.dump(client_secret_data, f, indent=4)

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
    if creds:
        service = build('gmail', 'v1', credentials=creds)
        message = create_message(to_addr, subject, body)
        send_message(service, 'me', message)
    else:
        raise ConnectionError("Gmail認証情報が無効です。")

# ---- 通知 ----
def tuuti(data_dict):
    print("tuuti:" + str(data_dict))
    if data_dict.get("notify_method") != "gmail":
        print("ℹ️ 通知は無効化されています。スキップします。")
        return

    global id, password, to
    to_addr = data_dict['gmail_address']
    subject = "✅ ダウンロード完了"
    file = f"{data_dict['file_name']}.{data_dict['format']}"
    file_encoded = urllib.parse.quote(file)

    body = (
        f"{data_dict['file_name']} が選択肢に追加されました\n"
        f"ダウンロードは以下URLからできます\n"
        f"https://kosukedownload.kesug.com/download.php?id={data_dict['user_id']}&pass={data_dict['password']}&download_file={file_encoded}\n\n"
        f"サイトのアクセスリンク: https://kosukedownload.kesug.com/index.php?id={data_dict['user_id']}&pass={data_dict['password']}"
        f"\n何か問題があった場合は返信してください"
    )

    try:
        send_gmail_notification(to_addr, subject, body)
        print("✅ Gmail通知送信完了")
    except Exception as e:
        print(f"❌ Gmail通知の送信中にエラーが発生しました: {e}")

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

def upload_ftp_file(ftp, local_path, ftp_path):
    with open(local_path, 'rb') as f:
        ftp.storbinary(f"STOR {ftp_path}", f)
    print(f"Uploaded {local_path} to {ftp_path}")

# ---- Google Drive 認証 ----
def authenticate_google_drive():
    client_secret_data = {}
    try:
        # 環境変数の文字列をPython辞書として安全に評価する
        client_secret_data = ast.literal_eval(CLIENT_SECRET1_CONTENT)
    except (ValueError, SyntaxError) as e:
        print(f"CLIENT_SECRET1_CONTENT の解析に失敗しました。JSON形式を確認してください: {e}")
        return None
        
    with open("client_secret.json", "w", encoding="utf-8") as f:
        # 辞書を厳密なJSON形式でファイルに書き出す
        json.dump(client_secret_data, f, indent=4)
        
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES_DRIVE)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES_DRIVE)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(file_path, file_name, folder_id=None):
    service = authenticate_google_drive()
    if service:
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Uploaded to Drive: {file_name}, File ID: {file['id']}")
        return file['id']
    else:
        raise ConnectionError("Google Drive認証情報が無効です。")

# ---- ファイルサイズ取得 ----
def get_file_size(file_path):
    return os.path.getsize(file_path)

# ---- ローカルリクエスト処理 ----
def process_local_requests():
    os.makedirs(LOCAL_REQUEST_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    exe_to_run = "python3"
    script_path = "./scripts/download.py"
    folder_path = DOWNLOAD_DIR

    for file_name in os.listdir(LOCAL_REQUEST_DIR):
        if not file_name.endswith('.json'):
            continue
        local_file = os.path.join(LOCAL_REQUEST_DIR, file_name)
        
        request = None
        
        try:
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # JSON形式とPython辞書形式の両方に対応するロジック
            try:
                request = json.loads(content)
            except json.JSONDecodeError:
                request = ast.literal_eval(content)
            
            if not isinstance(request, dict):
                raise ValueError("Parsed content is not a dictionary.")
                
        except Exception as e:
            print(f"Error processing {local_file}: Could not parse file. Details: {e}")
            if os.path.exists(local_file):
                os.remove(local_file)
            continue

        # グローバル変数に値をセット
        global ID, id, to, password
        ID = request.get('user_id')
        id = ID
        password = request.get('password')
        to = request.get('gmail_address')

        url = request.get('url')
        file_name_clean = re.sub(r'[<>:"/\\|?*]', '', request.get('file_name', ''))
        mode = {'mp3': 'audio', 'mp4': 'video'}.get(request.get('format'))
        
        if not all([url, file_name_clean, ID, password, to, mode]):
            print(f"Invalid or missing data in request file: {local_file}")
            if os.path.exists(local_file):
                os.remove(local_file)
            continue

        command = [
            exe_to_run,
            script_path,
            url,
            folder_path,
            file_name_clean,
            mode,
            local_file
        ]
        print(f"Running command: {' '.join(command)}")
        subprocess.run(command)

        downloaded_file_path = os.path.join(folder_path, f"{file_name_clean}.{request['format']}")
        try:
            if os.path.exists(downloaded_file_path):
                file_size = get_file_size(downloaded_file_path)
                print(f"File size: {file_size / (1024*1024):.2f} MB")
                
                tuuti(request)

                ftp = ftp_connect()
                try:
                    ftp_file_path = f"/upload_contents/{ID}/{file_name_clean}.{request['format']}"
                    upload_ftp_file(ftp, downloaded_file_path, ftp_file_path)
                finally:
                    ftp.quit()

                upload_file_to_drive(downloaded_file_path, f"{file_name_clean}.{request['format']}")

                os.remove(downloaded_file_path)
            
            if os.path.exists(local_file):
                os.remove(local_file)

        except Exception as e:
            print(f"Error processing {local_file}: {e}")
            if os.path.exists(downloaded_file_path):
                os.remove(downloaded_file_path)
            if os.path.exists(local_file):
                os.remove(local_file)

# ---- メイン処理 ----
def main_loop():
    os.makedirs(LOCAL_REQUEST_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    process_local_requests()

if __name__ == "__main__":
    main_loop()
