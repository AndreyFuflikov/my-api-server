from flask import Flask, request, send_file, abort
import os
import secrets
import tempfile

app = Flask(__name__)

# Временное хранилище: {file_id: file_path}
files_store = {}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Нет файла", 400
    
    file = request.files['file']
    if file.filename == '':
        return "Файл не выбран", 400
    
    # Генерируем уникальный ID
    file_id = secrets.token_urlsafe(8)
    
    # Сохраняем файл временно
    temp_file = os.path.join(tempfile.gettempdir(), file_id)
    file.save(temp_file)
    
    # Сохраняем путь и имя
    files_store[file_id] = {
        'path': temp_file,
        'filename': file.filename
    }
    
    return file_id

@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id not in files_store:
        abort(404)
    
    file_info = files_store[file_id]
    try:
        return send_file(
            file_info['path'],
            as_attachment=True,
            download_name=file_info['filename']
        )
    finally:
        # Удаляем файл сразу после скачивания (даже при ошибке)
        try:
            os.unlink(file_info['path'])
            del files_store[file_id]
        except:
            pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
