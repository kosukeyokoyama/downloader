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
        # ファイルの中身を読み込む際に、json.loadの前に安全な評価を試みる
        try:
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 最初にjson.loadsで試行
                request = json.loads(content)
        except json.JSONDecodeError:
            # JSONデコードに失敗した場合、ast.literal_evalでPython辞書として評価
            try:
                request = ast.literal_eval(content)
            except Exception as e:
                print(f"Error processing {local_file}: Could not parse file as valid JSON or Python literal. Details: {e}")
                os.remove(local_file)
                continue
        except Exception as e:
            print(f"An unexpected error occurred while processing {local_file}: {e}")
            os.remove(local_file)
            continue

        if not isinstance(request, dict):
            print(f"Error processing {local_file}: Parsed content is not a dictionary.")
            os.remove(local_file)
            continue

        url = request.get('url')
        if not isinstance(url, str):
            print(f"Invalid URL type in request: {type(url)}")
            os.remove(local_file)
            continue

        file_name_clean = re.sub(r'[<>:"/\\|?*]', '', request.get('file_name', ''))
        if not file_name_clean:
            print(f"Invalid file_name in request: {request.get('file_name', 'N/A')}")
            os.remove(local_file)
            continue

        global ID, id, to, password
        ID = request.get('user_id')
        id = ID
        password = request.get('password')
        to = request.get('gmail_address')
        mode = {'mp3': 'audio', 'mp4': 'video'}.get(request.get('format'))
        
        if mode is None:
            print(f"Unsupported format: {request.get('format', 'N/A')}")
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

        except Exception as e:
            print(f"Error processing {local_file}: {e}")
            # エラー時もクリーンアップを実行
            if os.path.exists(downloaded_file_path):
                os.remove(downloaded_file_path)
            if os.path.exists(local_file):
                os.remove(local_file)
