from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
TRANSLATED_FOLDER = 'translated'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(TRANSLATED_FOLDER):
    os.makedirs(TRANSLATED_FOLDER)

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    filename = file.filename
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    # 模拟翻译，生成翻译后的文件
    translated_filename = "translated_" + filename
    file.save(os.path.join(TRANSLATED_FOLDER, translated_filename))
    return jsonify({'filename': filename, 'translated_filename': translated_filename}), 200

@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/translated/<filename>')
def get_translated_file(filename):
    return send_from_directory(TRANSLATED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
