import os
import time
import json
import subprocess
from ftplib import FTP
import re
import urllib.parse
import requests
from email.mime.text import MIMEText
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import pathlib
from pywebpush import webpush, WebPushException
id = ""
password = ""
to = ""
SCOPES1 = ['https://www.googleapis.com/auth/gmail.send']
def gmail_authenticate():
    creds = None
    if os.path.exists('token1.json'):
        creds = Credentials.from_authorized_user_file('token1.json', SCOPES1)
    # トークンがないか期限切れなら再認証
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', 
                SCOPES1
            )

            creds = flow.run_local_server(port=8080)
        # トークン保存
        with open('token1.json', 'w') as token:
            token.write(creds.to_json())
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

def main():
    creds = gmail_authenticate()
    service = build('gmail', 'v1', credentials=creds)

    to = 'yokoyoko.yobi@gmail.com'          # 送り先
    subject = 'テストメール'
    body = 'これはGmail APIを使ったテストメールです。'

    message = create_message(to, subject, body)
    send_message(service, 'me', message)

def send_gmail_notification(to, subject, body):
    creds = gmail_authenticate()
    service = build('gmail', 'v1', credentials=creds)
    message = create_message(to, subject, body)
    send_message(service, 'me', message)

def tuuti(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 通知方法が 'gmail' 以外ならスキップ
    if data.get("notify_method") != "gmail":
        print("ℹ️ 通知は無効化されています。スキップします。")
        os.remove(file_path)
        return

    global id, password, to
    to1 = to  # 送り先メールアドレス
    subject = "✅ ダウンロード完了"

    # ファイル名をURLエンコードして安全に
    file = f"{data['file_name']}.{data['format']}"
    file_encoded = urllib.parse.quote(file)

    body = (
        f"{data['file_name']} が選択肢に追加されました\n"
        f"ダウンロードは以下URLからできます\n"
        f"https://kosukedownload.kesug.com/download.php?id={id}&pass={password}&download_file={file_encoded}\n\n"
        f"サイトのアクセスリンク: https://kosukedownload.kesug.com/index.php?id={id}&pass={password}"
        f"何か問題があった場合は返信してください"
    )

    send_gmail_notification(to1, subject, body)
    print("✅ Gmail通知送信完了")

    os.remove(file_path)



FTP_HOST = 'ftpupload.net'
FTP_USER = 'if0_39375859'
FTP_PASS = 'tbxgNOfYXIk'
FTP_REQUEST_DIR = '/htdocs/upload_requests'
FTP_UPLOAD_DIR = '/upload_contents'
LOCAL_REQUEST_DIR = 'request'
DOWNLOAD_DIR = 'download'
ID = ""

VAPID_PUBLIC_KEY = "BFVcfd2sDGF966JRkxKI4zllAE_eY5bQIrgVfs08B2SvnIqhniX3yuab36dR1wsvM6hJjRp17WkLUTjcxIomorE"
VAPID_PRIVATE_KEY = "pMsBC5Kob91fRlT5sRBy-gM6SIrLWC2JouVjTm1_Urs"
VAPID_CLAIMS = {
    "sub": "mailto:example@example.com"
}

def get_file_size(file_path):
    print(os.path.getsize(file_path))
    return os.path.getsize(file_path)
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

def upload_ftp_file(ftp, local_path, ftp_path, local):
    with open(local_path, 'rb') as f:
        ftp.storbinary(f"STOR " + ftp_path, f)
        tuuti(local)
    print(f"Uploaded {local_path} to {ftp_path}")


def process_ftp_requests():
    ftp = ftp_connect()
    print("start")
    try:
        files = list_ftp_files(ftp, FTP_REQUEST_DIR)
        for file_name in files:
            if not file_name.endswith('.json'):
                continue
            local_file = os.path.join(LOCAL_REQUEST_DIR, file_name)
            if os.path.exists(local_file):
                continue
            ftp_file_path = FTP_REQUEST_DIR + '/' + file_name
            print(f"Downloading JSON from FTP: {file_name}")
            download_ftp_file(ftp, ftp_file_path, local_file)
            remove_ftp_file(ftp, ftp_file_path)
            print(f"Deleted JSON from FTP: {file_name}")
    finally:
        ftp.quit()

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
        folderPath = r"C:\Python\Web\download"
        exeToRun = r"python"
        scriptPath = r"C:\Python\Web\downloader.py"
        url = request.get('url')
        if not isinstance(url, str):
            print(f"Invalid URL type in request: {type(url)}")
            os.remove(local_file)
            continue
        url_encoded = urllib.parse.quote(url, safe=":/?&=")

        fileName = re.sub(r'[<>:"/\\|?*]', '', request['file_name'])
        global ID
        ID = request['user_id']
        global id
        global to
        global password
        id = ID
        password = request['password']
        to = request['gmail_address']
        mode = {'mp3': 'audio', 'mp4': 'video'}.get(request['format'])
        if mode is None or fileName == "":
            print(f"Unsupported format: {request['format']}")
            os.remove(local_file)
            continue

        command = [
            exeToRun,
            scriptPath,
            f'"{url_encoded}"',
            folderPath,
            fileName,
            mode,
            local_file
        ]
        print(f"Running command: {' '.join(command)}")
        subprocess.run(command, shell=True)

        downloaded_file_path = os.path.join(folderPath, fileName + '.' + request['format'])

        try:
            file_size = get_file_size(downloaded_file_path)
            print(f"File size: {file_size / (1024 * 1024):.2f} MB")

            if file_size > 9 * 1024 * 1024:
                upload_file(downloaded_file_path, f"{fileName}.{request['format']}", local_file)
            else:
                ftp = ftp_connect()
                try:
                    ftp_file_path = f"/upload_contents/{ID}/{fileName}.{request['format']}"
                    print(f"Uploading to FTP: {ftp_file_path}")
                    upload_ftp_file(ftp, downloaded_file_path, ftp_file_path,local_file)
                    os.remove(downloaded_file_path)
                finally:
                    ftp.quit()
        except Exception as e:
            print(f"Error processing {local_file}: {e}")
        print(f"Removed local JSON: {file_name}")


SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_google_drive():
    creds = None
    # 'token.json' が存在する場合、その内容を使用
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 認証情報が無効であれば、再認証を実行
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # OAuth認証フローを開始
# OAuth2 認証フロー
            flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json', 
    SCOPES, 
    redirect_uri='http://localhost:8080/'
)

            creds = flow.run_local_server(port=8080)
        
        # 新しい認証情報を token.json として保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    drive_service = build('drive', 'v3', credentials=creds)
    
    return drive_service  # 返すのは drive_service

def upload_file(file_path, file_name, local, folder_id="1WQ0KztbP5jnCq-mSnCcBA2Hu5J6-M1ih"):
    # Google Drive 認証サービスの取得
    service = authenticate_google_drive()

    # メタデータを設定
    file_metadata = {'name': file_name}

    # フォルダを指定する場合
    if folder_id:
        file_metadata['parents'] = [folder_id]

    # メディア（アップロードするファイル）を準備
    media = MediaFileUpload(file_path, resumable=True)

    # Google Drive にファイルをアップロード
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print(f'File uploaded. File ID: {file["id"]}')
    file_id = file['id']
    add_to_uploaded_json(f"/{ID}/{file_name}.txt", file_id)
    # ダウンロードリンクを生成

    file_link = f"https://drive.google.com/uc?export=download&id={file_id}"       
    ftp = ftp_connect()
    add_url_to_ftp(ftp,file_name,file_link,file_path,local)

    print(f"Download link: {file_link}")  # ダウンロードリンクを表示
    return file_link
def add_url_to_ftp(ftp, file_name, file_url, filepath,local):
    ftp_file_path = f"/upload_contents/{ID}/{file_name}.txt"
    try:
        with open('temp_file.txt', 'w', encoding='utf-8') as f:
            f.write(file_url)

        with open('temp_file.txt', 'rb') as f:
            ftp.storbinary(f"STOR {ftp_file_path}", f)

        print(f"Uploaded content to {ftp_file_path}")
    finally:
        try:
            ftp.quit()
            tuuti(local)
        except:
            pass
        if os.path.exists('temp_file.txt'):
            os.remove('temp_file.txt')
        if os.path.exists(filepath):
            os.remove(filepath)
        print(f"Added URL to FTP as {ftp_file_path}: {file_url}")
def load_uploaded_json(json_path="uploaded_files.json"):
    if not os.path.exists(json_path):
        return {}
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_uploaded_json(data, json_path="uploaded_files.json"):
    with open(json_path, 'w', encoding='utf-8') as f:
        print("ok")
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_to_uploaded_json(filename, file_id, json_path="uploaded_files.json"):
    data = load_uploaded_json(json_path)
    data[filename] = file_id  # ← 上書きじゃなくて追加
    save_uploaded_json(data, json_path)

def list_all_ftp_files(ftp, path='/upload_contents'):
    all_files = []
    def _walk(p):
        try:
            ftp.cwd(p)
            items = []
            ftp.retrlines('NLST', items.append)
            for item in items:
                if item in ('.', '..'):
                    continue  # ← ここ追加！

                full_path = f"{p}/{item}"
                try:
                    ftp.cwd(full_path)
                    _walk(full_path)  # ディレクトリなら再帰
                except Exception as e:
                    all_files.append(full_path)

        except Exception as e:
            print(f"[error] FTPエラー on cwd({p}): {e}")
    _walk(path)
    return all_files



def cleanup_drive_files():
    """
    Google Drive 上のファイルを、対応する .txt ファイルが FTP に存在しない場合に削除する。
    uploaded_files.json を照合元とし、Drive 上から削除＋記録を更新。
    """
    drive_service = authenticate_google_drive()
    record_file = "uploaded_files.json"

    # jsonがなければ何もしない
    if not os.path.exists(record_file):
        return
    print("json")
    with open(record_file, "r", encoding="utf-8") as f:
        records = json.load(f)
    print("json_yomikomi")
    ftp = ftp_connect()
    print("ftp_ok")
    ftp.cwd('/upload_contents')
    ftp_files = list_all_ftp_files(ftp)
    print("get_file_ok")
    new_records = {}
    ftp_files_basename = set(os.path.basename(f) for f in ftp_files)

    for txt_path, file_id in records.items():
        base_txt_filename = os.path.basename(txt_path)
        if base_txt_filename in ftp_files_basename:
            new_records[txt_path] = file_id
        else:
            drive_service.files().delete(fileId=file_id).execute()
            print(f"🔁 Driveファイル削除: {txt_path}")
            
    ftp.quit()

    # 記録を更新
    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(new_records, f, indent=2)

def main_loop():
    authenticate_google_drive()
    os.makedirs(LOCAL_REQUEST_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    while True:
        try:
            check_dir = pathlib.Path(r'C:\Python\Web\download')
            for file in check_dir.iterdir():
                if file.is_file():
                    file.unlink()
            #cleanup_drive_files() 
            process_ftp_requests()  # ftp.quit() 内部で処理
        except Exception as e:
            print(f"FTP error: {e}")
        process_local_requests()
        time.sleep(0.1)

if __name__ == "__main__":
    main_loop()
