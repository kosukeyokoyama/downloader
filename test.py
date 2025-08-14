import os

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
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"--- File: {local_file} ---")
            print(content)
            print("-----------------------")
            
        except Exception as e:
            print(f"Error reading file {local_file}: {e}")

# この部分を追加して関数を呼び出します
if __name__ == '__main__':
    process_local_requests()
