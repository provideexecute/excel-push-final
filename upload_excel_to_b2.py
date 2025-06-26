import os
import base64
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from b2sdk.v2 import InMemoryAccountInfo, B2Api

load_dotenv()
app = Flask(__name__)
UPLOAD_FOLDER = 'static/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APP_KEY = os.getenv("B2_APP_KEY")
B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")

def upload_to_b2(file_path, file_name):
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
    bucket = b2_api.get_bucket_by_name(B2_BUCKET_NAME)
    with open(file_path, "rb") as f:
        bucket.upload_bytes(f.read(), file_name)
    return f"https://f000.backblazeb2.com/file/{B2_BUCKET_NAME}/{file_name}"

@app.route("/")
def index():
    return render_template("save_form.html")

@app.route("/save-local", methods=["POST"])
def save_local():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        filename = secure_filename(uploaded_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(file_path)
        return redirect(url_for("upload", filename=filename))
    return "❌ Ошибка: файл не выбран"

@app.route("/upload")
def upload():
    filename = request.args.get("filename")
    return render_template("upload.html", filename=filename)

@app.route("/receive", methods=["POST"])
def receive():
    filename = request.form['filename']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return f"❌ Файл {filename} не найден в {UPLOAD_FOLDER}"
    with open(file_path, "rb") as f:
        base64_data = base64.b64encode(f.read()).decode("utf-8")
        with open(file_path + ".b64.txt", "w") as b64file:
            b64file.write(base64_data)
    try:
        url = upload_to_b2(file_path, filename)
        return f"<p>✅ Загружено в B2: <a href='{url}'>{url}</a></p>"
    except Exception as e:
        return f"<p>❌ Ошибка загрузки: {str(e)}</p>"

@app.route("/static/tmp/<filename>")
def serve_tmp_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
