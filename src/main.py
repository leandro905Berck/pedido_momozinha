import os
import sys
import json
import uuid

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
# from src.models.user import db # Not needed for this project
# from src.routes.user import user_bp # Not needed for this project

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
IMAGES_JSON_PATH = os.path.join(DATA_FOLDER, 'images.json')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload and data folders exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)
if not os.path.exists(IMAGES_JSON_PATH):
    with open(IMAGES_JSON_PATH, 'w') as f:
        json.dump([], f)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    caption = request.form.get('caption', '')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Generate a unique filename to prevent overwrites and issues with special characters
        filename_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{filename_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        try:
            with open(IMAGES_JSON_PATH, 'r+') as f:
                images_data = json.load(f)
                images_data.append({'filename': unique_filename, 'caption': caption})
                f.seek(0)
                json.dump(images_data, f, indent=4)
                f.truncate()
        except (IOError, json.JSONDecodeError) as e:
            # If file is empty or corrupted, initialize with new data
            with open(IMAGES_JSON_PATH, 'w') as f:
                json.dump([{'filename': unique_filename, 'caption': caption}], f, indent=4)
        
        return jsonify({'message': 'File uploaded successfully', 'filename': unique_filename, 'caption': caption}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/get_images', methods=['GET'])
def get_images():
    try:
        with open(IMAGES_JSON_PATH, 'r') as f:
            images_data = json.load(f)
        return jsonify(images_data), 200
    except FileNotFoundError:
        return jsonify([]), 200 # Return empty list if file doesn't exist
    except json.JSONDecodeError:
        return jsonify({'error': 'Error reading image data'}), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        # Serve specific files like CSS, JS, or other HTML pages
        if path.endswith('.html') and path != 'index.html': # for sim.html
             return send_from_directory(static_folder_path, path)
        elif not path.endswith('.html'): # for static assets like css, js, images
            return send_from_directory(static_folder_path, path)
        # Fall through to index.html for other paths if not a direct file match
    
    # Default to serving index.html
    index_path = os.path.join(static_folder_path, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_folder_path, 'index.html')
    else:
        # A basic index.html as a fallback if not present
        # In a real scenario, the create_flask_app should provide a basic one.
        # Or, we should create one in the next steps.
        return "index.html not found. Please create one in the static folder.", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

