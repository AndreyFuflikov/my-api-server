from flask import Flask, request, jsonify
import json, os

app = Flask(__name__)
DATA_FILE = 'data.json'

# Инициализация данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

data_store = load_data()

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API работает! Используйте /items"})

@app.route('/items', methods=['GET'])
def get_items():
    return jsonify(data_store)

@app.route('/items', methods=['POST'])
def add_item():
    item = request.json
    data_store.append(item)
    save_data(data_store)
    return jsonify({"id": len(data_store)-1, "item": item}), 201

@app.route('/items/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
def item_ops(item_id):
    if 0 <= item_id < len(data_store):
        if request.method == 'GET':
            return jsonify(data_store[item_id])
        elif request.method == 'PUT':
            data_store[item_id] = request.json
            save_data(data_store)
            return jsonify(data_store[item_id])
        elif request.method == 'DELETE':
            deleted = data_store.pop(item_id)
            save_data(data_store)
            return jsonify({"deleted": deleted})
    return jsonify({"error": "Item not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
