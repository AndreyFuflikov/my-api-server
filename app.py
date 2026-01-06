from flask import Flask, request, send_file, abort
import os
import secrets
import tempfile

app = Flask(__name__)
files_store = {}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Нет файла", 400
    
    file = request.files['file']
    if file.filename == '':
        return "Файл не выбран", 400
    
    file_id = secrets.token_urlsafe(10)  # 10 символов для надёжности
    temp_file = os.path.join(tempfile.gettempdir(), file_id)
    file.save(temp_file)
    
    files_store[file_id] = {
        'path': temp_file,
        'filename': file.filename
    }
    print(f"📤 Загружен: {file.filename} → ID: {file_id}")
    
    return file_id

@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id not in files_store:
        print(f"❌ Файл {file_id} не найден")
        abort(404)
    
    file_info = files_store[file_id]
    
    # ✅ ПРОСТОЙ send_file — БЕЗ удаления!
    try:
        response = send_file(
            file_info['path'],
            as_attachment=True,
            download_name=file_info['filename'],
            mimetype='application/octet-stream'
        )
        print(f"✅ Файл {file_id} отправлен")
        return response
    except Exception as e:
        print(f"❌ Ошибка отправки {file_id}: {e}")
        abort(500)

@app.route('/', methods=['GET'])
def status():
    return "Сервер работает! Загрузка: POST /upload, Скачивание: GET /download/ID"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
