import os

# 注: このスクリプトは、元のプログラムの一部です。
# 動作させるには、他の関数や変数が定義されている必要があります。

def process_local_requests():
    os.makedirs(LOCAL_REQUEST_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    for file_name in os.listdir(LOCAL_REQUEST_DIR):
        # .json ファイルのみを対象とします
        if not file_name.endswith('.json'):
            continue
        
        local_file = os.path.join(LOCAL_REQUEST_DIR, file_name)
        
        try:
            # ファイルを読み込みモードで開き、内容をすべて読み込みます
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 読み込んだ内容をそのまま表示します
            print(f"--- File: {local_file} ---")
            print(content)
            print("-----------------------")
            
        except Exception as e:
            print(f"Error reading file {local_file}: {e}")
