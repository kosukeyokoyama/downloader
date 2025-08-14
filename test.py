import os
import json

# 注: 以下の定数は、元のプログラムを想定して定義しています。
# 実際の環境に合わせて値を調整してください。
LOCAL_REQUEST_DIR = "upload_requests"
DOWNLOAD_DIR = "download"

def process_local_requests():
    os.makedirs(LOCAL_REQUEST_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # 処理すべきファイルがあるか確認
    if not os.path.exists(LOCAL_REQUEST_DIR) or not os.listdir(LOCAL_REQUEST_DIR):
        print("info: 'upload_requests' ディレクトリに処理すべきファイルはありません。")
        return

    for file_name in os.listdir(LOCAL_REQUEST_DIR):
        if not file_name.endswith('.json'):
            continue
        
        local_file = os.path.join(LOCAL_REQUEST_DIR, file_name)
        
        try:
            # json.load を使用してファイルをデコードします
            with open(local_file, 'r', encoding='utf-8') as f:
                request_data = json.load(f)
            
            # デコードした内容（辞書オブジェクト）を表示します
            print(f"--- File: {local_file} ---")
            print("Successfully decoded JSON file. Data type:", type(request_data))
            print("Content:", request_data)
            print("-----------------------")
            
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON file {local_file}: {e}")
        except Exception as e:
            print(f"Error reading file {local_file}: {e}")

if __name__ == '__main__':
    process_local_requests()
