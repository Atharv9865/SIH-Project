from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
import uuid
import cv2
import numpy as np
from datetime import datetime
import database as db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'swachhata-sentinel-secret'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db.init_db()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def analyze_waste_image(image_path):
    """
    Placeholder for ML waste classification
    In a real implementation, this would use a trained model
    """
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        return {"category": "unknown", "confidence": 0, "severity": 0}
    
    # Simple color-based analysis (placeholder)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Detect dominant colors
    # This is a simplified approach - real implementation would use ML
    green_mask = cv2.inRange(hsv, (36, 25, 25), (70, 255, 255))
    brown_mask = cv2.inRange(hsv, (10, 100, 20), (20, 255, 200))
    blue_mask = cv2.inRange(hsv, (90, 50, 50), (130, 255, 255))
    
    green_count = cv2.countNonZero(green_mask)
    brown_count = cv2.countNonZero(brown_mask)
    blue_count = cv2.countNonZero(blue_mask)
    
    total_pixels = img.shape[0] * img.shape[1]
    
    # Determine waste type based on color distribution
    if green_count > brown_count and green_count > blue_count:
        category = "organic"
        confidence = min(green_count / total_pixels * 3, 0.95)
    elif brown_count > blue_count:
        category = "mixed"
        confidence = min(brown_count / total_pixels * 3, 0.95)
    else:
        category = "plastic"
        confidence = min(blue_count / total_pixels * 3, 0.95)
    
    # Calculate severity (0-10 scale)
    # This is simplified - real implementation would be more sophisticated
    non_green_ratio = 1 - (green_count / total_pixels)
    severity = min(round(non_green_ratio * 10, 1), 10)
    
    return {
        "category": category,
        "confidence": round(confidence, 2),
        "severity": severity
    }

@app.route('/')
def index():
    """Render the main map page"""
    zones = db.get_all_zones()
    return render_template('map.html', zones=zones)

@app.route('/api/photos', methods=['GET'])
def get_photos():
    """Get all photos or photos within a bounding box"""
    if all(param in request.args for param in ['north', 'south', 'east', 'west']):
        # Get photos within bounding box
        north = float(request.args.get('north'))
        south = float(request.args.get('south'))
        east = float(request.args.get('east'))
        west = float(request.args.get('west'))
        photos = db.get_photos_in_bounds(north, south, east, west)
    else:
        # Get all photos
        photos = db.get_all_photos()
    
    return jsonify(photos)

@app.route('/api/photos/<int:photo_id>', methods=['GET'])
def get_photo(photo_id):
    """Get a specific photo by ID"""
    photo = db.get_photo_by_id(photo_id)
    if photo:
        return jsonify(photo)
    return jsonify({"error": "Photo not found"}), 404

@app.route('/api/zones', methods=['GET'])
def get_zones():
    """Get all waste zones"""
    zones = db.get_all_zones()
    return jsonify(zones)

@app.route('/api/upload', methods=['POST'])
def upload_photo():
    """Handle photo upload with location data"""
    if 'photo' not in request.files:
        return jsonify({"error": "No photo part"}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400
    
    # Get location data
    try:
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid location data"}), 400
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Analyze waste in image
    analysis = analyze_waste_image(filepath)
    
    # Save to database
    photo_id = db.add_photo(
        filepath, 
        latitude, 
        longitude, 
        analysis['category'],
        analysis['severity'],
        analysis['confidence']
    )
    
    # Get the zone this photo belongs to
    zone = db.get_zone_by_location(latitude, longitude)
    
    # Emit real-time update via WebSocket
    socketio.emit('new_photo', {
        'photo_id': photo_id,
        'image_path': filepath,
        'latitude': latitude,
        'longitude': longitude,
        'timestamp': datetime.now().isoformat(),
        'analysis': analysis,
        'zone': zone
    })
    
    return jsonify({
        "success": True,
        "photo_id": photo_id,
        "analysis": analysis
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)