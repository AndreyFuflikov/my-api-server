from flask import Flask, request, Response, abort
import os
import secrets
import tempfile
import mimetypes

app = Flask(__name__)
files_store = {}

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
    print(f"📤 Загружен файл: {file.filename} (ID: {file_id})")
    
    return file_id

@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id not in files_store:
        abort(404)
    
    file_info = files_store[file_id]
    if file_info['downloaded']:
        print(f"❌ Файл {file_id} уже скачан")
        del files_store[file_id]
        abort(404)
    
    try:
        with open(file_info['path'], 'rb') as f:
            data = f.read()
        
        file_info['downloaded'] = True
        
        # Устанавливаем заголовки
        filename = file_info['filename']
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        response = Response(
            data,
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(data))
            }
        )
        
        # Удаляем файл ПОСЛЕ отправки
        try:
            os.unlink(file_info['path'])
            del files_store[file_id]
            print(f"✅ Файл {file_id} скачан и удалён")
        except:
            pass
            
        return response
        
    except Exception as e:
        print(f"❌ Ошибка скачивания {file_id}: {e}")
        abort(500)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
