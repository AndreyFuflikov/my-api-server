from flask import Flask, request, jsonify, send_file, abort
import os
import secrets
import tempfile
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Хранилище файлов (имитация БД)
FILES_DIR = os.path.join(tempfile.gettempdir(), 'installer_files')
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

files_db = {}  # {id: {'name': str, 'path': str, 'size': int, 'version': str}}

@app.route('/status')
def status():
    return jsonify({"status": "ok", "files_count": len(files_db)})

@app.route('/files')
def get_files():
    """Список всех файлов"""
    files_list = []
    for file_id, info in files_db.items():
        stat = os.stat(info['path'])
        files_list.append({
            'id': file_id,
            'name': info['name'],
            'size': stat.st_size,
            'version': info.get('version', '1.0')
        })
    return jsonify(files_list)

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    """Загрузка файла (админ)"""
    if 'file' not in request.files:
        return "Нет файла", 400
    
    file = request.files['file']
    if file.filename == '':
        return "Файл не выбран", 400
    
    file_id = secrets.token_urlsafe(12)
    filename = secure_filename(file.filename)
    file_path = os.path.join(FILES_DIR, file_id)
    
    file.save(file_path)
    
    files_db[file_id] = {
        'name': filename,
        'path': file_path,
        'version': request.form.get('version', '1.0')
    }
    
    return jsonify({'id': file_id, 'message': 'Загружен успешно'}), 200

@app.route('/download/<file_id>')
def download_file(file_id):
    """Скачивание файла"""
    if file_id not in files_db:
        abort(404)
    
    file_info = files_db[file_id]
    return send_file(file_info['path'], 
                    as_attachment=True, 
                    download_name=file_info['name'])

@app.route('/admin/file/<file_id>', methods=['DELETE'])
def admin_delete(file_id):
    """Удаление файла (админ)"""
    if file_id in files_db:
        try:
            os.unlink(files_db[file_id]['path'])
            del files_db[file_id]
            return jsonify({'message': 'Удалено'}), 200
        except:
            pass
    abort(404)

@app.route('/admin/file/<file_id>/rename', methods=['PUT'])
def admin_rename(file_id):
    """Переименование (админ)"""
    data = request.get_json()
    if file_id in files_db and data.get('name'):
        files_db[file_id]['name'] = secure_filename(data['name'])
        return jsonify({'message': 'Переименовано'}), 200
    abort(400)

@app.route('/')
def index():
    return '''
    <h1>🚀 Сервер установщика программ</h1>
    <p>✅ Готов к работе!</p>
    <ul>
        <li>GET /files - список программ</li>
        <li>POST /admin/upload - загрузка (админ)</li>
        <li>GET /download/:id - скачивание</li>
    </ul>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
