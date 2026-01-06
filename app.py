from flask import Flask, request, send_file, abort
import os
import secrets
import tempfile
from functools import wraps

app = Flask(__name__)
files_store = {}

def check_downloaded(file_id):
    """Проверяет, был ли файл уже скачан"""
    return files_store.get(file_id, {}).get('downloaded', False)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Нет файла", 400
    
    file = request.files['file']
    if file.filename == '':
        return "Файл не выбран", 400
    
    file_id = secrets.token_urlsafe(8)
    temp_file = os.path.join(tempfile.gettempdir(), file_id)
    file.save(temp_file)
    
    files_store[file_id] = {
        'path': temp_file,
        'filename': file.filename,
        'downloaded': False
    }
    
    return file_id

@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id not in files_store:
        abort(404)
    
    file_info = files_store[file_id]
    if file_info['downloaded']:
        del files_store[file_id]
        abort(404)
    
    @wraps(send_file)
    def wrapped_send_file():
        file_info['downloaded'] = True
        response = send_file(
            file_info['path'],
            as_attachment=True,
            download_name=file_info['filename']
        )
        # Удаляем ПОСЛЕ отправки
        try:
            os.unlink(file_info['path'])
            del files_store[file_id]
        except:
            pass
        return response
    
    return wrapped_send_file()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
