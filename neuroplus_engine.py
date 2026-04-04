import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
import exifread
from dotenv import load_dotenv
from database import get_all_quests, get_hero_data, add_submission, get_pending_submissions, approve_submission, get_quest, add_quest, remove_quest
import time
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_neuroplus_key"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def extract_metadata(filepath):
    try:
        metadata = {}
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
            # Simple timestamp extraction
            if 'Image DateTime' in tags:
                metadata['timestamp'] = str(tags['Image DateTime'])
            elif 'EXIF DateTimeOriginal' in tags:
                metadata['timestamp'] = str(tags['EXIF DateTimeOriginal'])
            else:
                # Fallback to file creation time
                metadata['timestamp'] = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")

            # Simple GPS checks
            if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
                metadata['location'] = "GPS Data Found"
            else:
                metadata['location'] = "No GPS Data"
                
        if not metadata.get('timestamp') or metadata['timestamp'] == 'None':
            metadata['timestamp'] = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")

        return metadata
    except Exception as e:
        return {"timestamp": datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S"), "location": "Unknown", "error": str(e)}

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    view_mode = session.get('view_mode', 'hero')
    hero_data = get_hero_data()
    quests = get_all_quests()
    pending = get_pending_submissions()
    
    return render_template('quest_hub.html', 
                           view_mode=view_mode, 
                           hero=hero_data, 
                           quests=quests, 
                           pending_submissions=pending,
                           is_parent=(view_mode == 'parent'),
                           has_pin=('parent_pin' in session))

@app.route('/toggle_view', methods=['POST'])
def toggle_view():
    data = request.json
    pin = data.get('pin', '')
    if session.get('view_mode') == 'parent':
        session['view_mode'] = 'hero'
        return jsonify({"success": True})
    
    if 'parent_pin' not in session:
        if not pin or len(pin) < 4:
            return jsonify({"success": False, "error": "PIN must be at least 4 characters"}), 400
        session['parent_pin'] = pin
        session['view_mode'] = 'parent'
        return jsonify({"success": True})
    
    if pin == session.get('parent_pin'):
        session['view_mode'] = 'parent'
        return jsonify({"success": True})
        
    return jsonify({"success": False, "error": "Invalid PIN"}), 403

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    
    file = request.files['file']
    quest_id = request.form.get('quest_id')
    sticker = request.form.get('sticker', '⭐')

    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
        
    if not quest_id:
        return jsonify({"success": False, "error": "Missing quest ID"}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{int(time.time())}_{filename}")
        file.save(filepath)
        
        metadata = extract_metadata(filepath)
        
        # Validation Logic (Flagging for parent)
        quest = get_quest(int(quest_id))
        metadata_status = "On Time"
        
        metadata['status_flag'] = metadata_status
        
        submission = add_submission(int(quest_id), filepath, metadata, sticker)
        
        return jsonify({"success": True, "submission": submission})

@app.route('/approve', methods=['POST'])
def approve():
    if session.get('view_mode') != 'parent':
        return jsonify({"success": False, "error": "Unauthorized"}), 403
        
    data = request.json
    sub_id = data.get('sub_id')
    
    if approve_submission(int(sub_id)):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Submission not found"}), 404

@app.route('/add_quest_endpoint', methods=['POST'])
def add_quest_endpoint():
    if session.get('view_mode') != 'parent':
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    icon = data.get('icon', '⭐')
    xp = data.get('xp', 50)
    
    if not title:
        return jsonify({"success": False, "error": "Missing title"}), 400
        
    quest = add_quest(title, description, icon, xp)
    return jsonify({"success": True, "quest": quest})

@app.route('/remove_quest_endpoint', methods=['POST'])
def remove_quest_endpoint():
    if session.get('view_mode') != 'parent':
        return jsonify({"success": False, "error": "Unauthorized"}), 403
        
    data = request.json
    quest_id = data.get('quest_id')
    
    if remove_quest(int(quest_id)):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Quest not found"}), 404

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)
