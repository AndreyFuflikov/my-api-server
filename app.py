from flask import Flask, jsonify, send_from_directory, abort, request
import os

app = Flask(__name__)

# Папка с программами относительно app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGES_DIR = os.path.join(BASE_DIR, "packages")

# Базовый URL сервера (для формирования ссылок в /files)
# На Render нужно заменить на ваш реальный URL (например, https://my-api-server-1-siht.onrender.com)
SERVER_BASE_URL = os.environ.get("SERVER_BASE_URL", "http://localhost:10000")


def scan_packages():
    """
    Сканирует папку packages и возвращает список файлов с размерами.
    """
    files = []
    if not os.path.exists(PACKAGES_DIR):
        return files

    for name in os.listdir(PACKAGES_DIR):
        path = os.path.join(PACKAGES_DIR, name)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            files.append({
                "id": name,                     # ID = имя файла
                "name": name,                   # отображаемое имя
                "size": size,                   # размер в байтах
                "version": "1.0",               # можно потом расширить
                "download_url": f"{SERVER_BASE_URL}/download/{name}"
            })
    return files


@app.route("/status")
def status():
    """
    Простой статус для клиента (экран загрузки).
    """
    files = scan_packages()
    return jsonify({
        "status": "ok",
        "files_count": len(files)
    })


@app.route("/files")
def get_files():
    """
    Возвращает список файлов в папке packages.
    """
    files = scan_packages()
    return jsonify(files)


@app.route("/download/<filename>")
def download_file(filename):
    """
    Скачивание файла из папки packages.
    """
    # Защита от попыток выйти за пределы папки
    if "/" in filename or "\\" in filename:
        abort(400)

    full_path = os.path.join(PACKAGES_DIR, filename)
    if not os.path.isfile(full_path):
        abort(404)

    # send_from_directory корректно выставляет заголовки и скачивание
    return send_from_directory(
        directory=PACKAGES_DIR,
        path=filename,
        as_attachment=True,
        download_name=filename
    )


@app.route("/")
def index():
    return """
    <h1>🚀 Сервер установщика (Git-папка packages)</h1>
    <p>Все программы лежат в папке <code>packages/</code> рядом с app.py.</p>
    <ul>
        <li>GET /status — статус сервера и кол-во файлов</li>
        <li>GET /files — список программ (JSON)</li>
        <li>GET /download/&lt;filename&gt; — скачивание файла</li>
    </ul>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)