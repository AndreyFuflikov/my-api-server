from flask import Flask, request, jsonify, send_file, abort
import os
import secrets
import sqlite3
import shutil
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)

# Постоянная папка для файлов
UPLOAD_DIR = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    """Инициализация БД"""
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files 
                 (id TEXT PRIMARY KEY, name TEXT, path TEXT, size INTEGER, version TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/status')
def status():
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM files')
    count = c.fetchone()[0]
    conn.close()
    return jsonify({"status": "ok", "files_count": count})

@app.route('/files')
def get_files():
    """Список всех файлов"""
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute('SELECT id, name, size, version FROM files')
    rows = c.fetchall()
    conn.close()
    
    files_list = []
    for row in rows:
        file_id, name, size, version = row
        files_list.append({
            'id': file_id,
            'name': name,
            'size': size,
            'version': version or '1.0'
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
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
    
    file.save(file_path)
    
    # Сохранить в БД
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    stat = os.stat(file_path)
    c.execute("INSERT INTO files (id, name, path, size, version) VALUES (?, ?, ?, ?, ?)",
              (file_id, filename, file_path, stat.st_size, request.form.get('version', '1.0')))
    conn.commit()
    conn.close()
    
    return jsonify({'id': file_id, 'message': 'Загружен успешно'}), 200

@app.route('/download/<file_id>')
def download_file(file_id):
    """Скачивание файла"""
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute("SELECT path, name FROM files WHERE id = ?", (file_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        abort(404)
    
    file_path, filename = row
    if not os.path.exists(file_path):
        # Удалить из БД если файл пропал
        conn = sqlite3.connect('files.db')
        c = conn.cursor()
        c.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        conn.close()
        abort(404)
    
    return send_file(file_path, 
                    as_attachment=True, 
                    download_name=filename)

@app.route('/admin/file/<file_id>', methods=['DELETE'])
def admin_delete(file_id):
    """Удаление файла (админ)"""
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute("SELECT path FROM files WHERE id = ?", (file_id,))
    row = c.fetchone()
    
    if row:
        file_path = row[0]
        try:
            os.unlink(file_path)
            c.execute("DELETE FROM files WHERE id = ?", (file_id,))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Удалено'}), 200
        except:
            conn.close()
            pass
    abort(404)

@app.route('/admin/file/<file_id>/rename', methods=['PUT'])
def admin_rename(file_id):
    """Переименование (админ)"""
    data = request.get_json()
    if not data or not data.get('name'):
        abort(400)
    
    new_name = secure_filename(data['name'])
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    c.execute("UPDATE files SET name = ? WHERE id = ?", (new_name, file_id))
    
    if c.rowcount > 0:
        conn.commit()
        conn.close()
        return jsonify({'message': 'Переименовано'}), 200
    
    conn.close()
    abort(404)

@app.route('/')
def index():
    return '''
    <h1>🚀 Сервер установщика программ (SQLite)</h1>
    <p>✅ Файлы НЕ исчезают при перезапуске!</p>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
