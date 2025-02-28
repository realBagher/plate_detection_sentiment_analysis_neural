import os
from flask import Flask, request, redirect, url_for, render_template_string, flash, send_from_directory
from engine.processor import image_processor, video_processor

# -----------------------------
# Configuration
# -----------------------------
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER
app.secret_key = "supersecretkey"


# -----------------------------
# Flask Routes
# -----------------------------
@app.route("/")
def index():
    return render_template_string("""
    <!doctype html>
    <html>
    <head>
      <title>Plate Detection App</title>
      <style>
        body { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; }
        h1 { text-align: center; color: #333; }
        nav { text-align: center; margin-bottom: 20px; }
        nav a { margin: 0 15px; text-decoration: none; color: #007BFF; }
        .upload-form { text-align: center; margin-bottom: 20px; }
        button { padding: 10px 20px; background: #007BFF; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Plate Detection App</h1>
        <nav>
          <a href="/">Upload</a>
          <a href="/gallery">Gallery</a>
        </nav>
        <div class="upload-form">
          <form method="POST" action="/upload" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <br><br>
            <button type="submit">Upload and Process</button>
          </form>
        </div>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul style="color:green;">
              {% for message in messages %}
                <li>{{ message }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
      </div>
    </body>
    </html>
    """)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("index"))
    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))
    filename = file.filename
    upload_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(upload_path)
    ext = os.path.splitext(filename)[1].lower()
    if ext in [".jpg", ".jpeg", ".png"]:
        image_processor(upload_path, app.config["PROCESSED_FOLDER"])
    elif ext in [".mp4", ".avi", ".mov"]:
        video_processor(upload_path, app.config["PROCESSED_FOLDER"], font_size=30)
    else:
        flash("Unsupported file type")
        return redirect(url_for("index"))
    flash("File uploaded and processed successfully!")
    return redirect(url_for("gallery"))


@app.route("/gallery")
def gallery():
    uploaded_files = os.listdir(app.config["UPLOAD_FOLDER"])
    processed_files = os.listdir(app.config["PROCESSED_FOLDER"])
    return render_template_string("""
    <!doctype html>
    <html>
    <head>
      <title>Gallery - Plate Detection App</title>
      <style>
        body { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; }
        h1 { text-align: center; color: #333; }
        nav { text-align: center; margin-bottom: 20px; }
        nav a { margin: 0 15px; text-decoration: none; color: #007BFF; }
        .section { margin-bottom: 40px; }
        .gallery { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }
        .gallery-item { background: #eaeaea; padding: 10px; border-radius: 4px; text-align: center; width: 300px; }
        .gallery-item img, .gallery-item video { width: 100%; height: auto; border-radius: 4px; }
        .links { margin-top: 10px; }
        .links a { text-decoration: none; margin: 0 5px; color: #007BFF; font-size: 0.9em; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Gallery</h1>
        <nav>
          <a href="/">Upload</a>
          <a href="/gallery">Gallery</a>
        </nav>
        <div class="section">
          <h2>Uploaded Files</h2>
          <div class="gallery">
            {% for file in uploaded_files %}
              <div class="gallery-item">
                {% if file.lower().endswith(('.jpg', '.jpeg', '.png')) %}
                  <a href="{{ url_for('uploaded_file', filename=file) }}" target="_blank">
                    <img src="{{ url_for('uploaded_file', filename=file) }}" alt="{{ file }}">
                  </a>
                {% elif file.lower().endswith(('.mp4', '.avi', '.mov')) %}
                  <a href="{{ url_for('uploaded_file', filename=file) }}" target="_blank">
                    <video controls>
                      <source src="{{ url_for('uploaded_file', filename=file) }}" type="video/mp4">
                      Your browser does not support the video tag.
                    </video>
                  </a>
                {% else %}
                  <p>{{ file }}</p>
                {% endif %}
                <div class="links">
                  <a href="{{ url_for('uploaded_file', filename=file) }}" target="_blank">Fullscreen</a>
                  <a href="{{ url_for('uploaded_file', filename=file) }}" download>Download</a>
                </div>
                <p>{{ file }}</p>
              </div>
            {% endfor %}
          </div>
        </div>
        <div class="section">
          <h2>Processed Files</h2>
          <div class="gallery">
            {% for file in processed_files %}
              <div class="gallery-item">
                {% if file.lower().endswith(('.jpg', '.jpeg', '.png')) %}
                  <a href="{{ url_for('processed_file', filename=file) }}" target="_blank">
                    <img src="{{ url_for('processed_file', filename=file) }}" alt="{{ file }}">
                  </a>
                {% elif file.lower().endswith(('.mp4', '.avi', '.mov')) %}
                  <a href="{{ url_for('processed_file', filename=file) }}" target="_blank">
                    <video controls>
                      <source src="{{ url_for('processed_file', filename=file) }}" type="video/mp4">
                      Your browser does not support the video tag.
                    </video>
                  </a>
                {% else %}
                  <p>{{ file }}</p>
                {% endif %}
                <div class="links">
                  <a href="{{ url_for('processed_file', filename=file) }}" target="_blank">Fullscreen</a>
                  <a href="{{ url_for('processed_file', filename=file) }}" download>Download</a>
                </div>
                <p>{{ file }}</p>
              </div>
            {% endfor %}
          </div>
        </div>
      </div>
    </body>
    </html>
    """, uploaded_files=uploaded_files, processed_files=processed_files)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/processed/<path:filename>")
def processed_file(filename):
    return send_from_directory(app.config["PROCESSED_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
