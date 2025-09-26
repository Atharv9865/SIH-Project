import sqlite3
import os
import json
from datetime import datetime

# Database configuration
DB_PATH = 'waste_management.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create photos table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_path TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        timestamp TEXT NOT NULL,
        waste_category TEXT,
        severity_score REAL,
        confidence REAL,
        is_verified BOOLEAN DEFAULT 0
    )
    ''')
    
    # Create zones table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        center_lat REAL NOT NULL,
        center_lng REAL NOT NULL,
        radius REAL NOT NULL,
        waste_level INTEGER NOT NULL,
        photo_count INTEGER DEFAULT 0,
        last_updated TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def add_photo(image_path, latitude, longitude, waste_category, severity_score, confidence):
    """Add a new photo to the database and update zones"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    cursor.execute('''
    INSERT INTO photos (image_path, latitude, longitude, timestamp, waste_category, severity_score, confidence, is_verified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (image_path, latitude, longitude, timestamp, waste_category, severity_score, confidence, False))
    
    photo_id = cursor.lastrowid
    
    # Update or create zone
    update_zone(latitude, longitude, severity_score)
    
    conn.commit()
    conn.close()
    
    return photo_id

def get_all_photos():
    """Get all photos from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, image_path, latitude, longitude, timestamp, waste_category, severity_score, confidence, is_verified
    FROM photos
    ORDER BY timestamp DESC
    ''')
    
    photos = []
    for row in cursor.fetchall():
        photos.append({
            'id': row['id'],
            'image_path': row['image_path'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'timestamp': row['timestamp'],
            'waste_category': row['waste_category'],
            'severity_score': row['severity_score'],
            'confidence': row['confidence'],
            'is_verified': bool(row['is_verified'])
        })
    
    conn.close()
    return photos

def get_photos_in_bounds(north, south, east, west):
    """Get photos within a geographic bounding box"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, image_path, latitude, longitude, timestamp, waste_category, severity_score, confidence, is_verified
    FROM photos
    WHERE latitude <= ? AND latitude >= ? AND longitude <= ? AND longitude >= ?
    ORDER BY timestamp DESC
    ''', (north, south, east, west))
    
    photos = []
    for row in cursor.fetchall():
        photos.append({
            'id': row['id'],
            'image_path': row['image_path'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'timestamp': row['timestamp'],
            'waste_category': row['waste_category'],
            'severity_score': row['severity_score'],
            'confidence': row['confidence'],
            'is_verified': bool(row['is_verified'])
        })
    
    conn.close()
    return photos

def get_photo_by_id(photo_id):
    """Get a specific photo by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, image_path, latitude, longitude, timestamp, waste_category, severity_score, confidence, is_verified
    FROM photos
    WHERE id = ?
    ''', (photo_id,))
    
    row = cursor.fetchone()
    if row:
        photo = {
            'id': row['id'],
            'image_path': row['image_path'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'timestamp': row['timestamp'],
            'waste_category': row['waste_category'],
            'severity_score': row['severity_score'],
            'confidence': row['confidence'],
            'is_verified': bool(row['is_verified'])
        }
        conn.close()
        return photo
    
    conn.close()
    return None

def update_zone(latitude, longitude, severity_score, radius=0.005):
    """Update or create a zone based on a new photo"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if a zone exists at this location
    cursor.execute('''
    SELECT id, waste_level, photo_count
    FROM zones
    WHERE ABS(center_lat - ?) < ? AND ABS(center_lng - ?) < ?
    ''', (latitude, radius, longitude, radius))
    
    zone = cursor.fetchone()
    timestamp = datetime.now().isoformat()
    
    if zone:
        # Update existing zone
        zone_id = zone['id']
        current_level = zone['waste_level']
        photo_count = zone['photo_count'] + 1
        
        # Calculate new waste level (0-10)
        # This is a simple weighted average - could be more sophisticated
        new_level = int((current_level * photo_count + severity_score) / (photo_count + 1))
        
        cursor.execute('''
        UPDATE zones
        SET waste_level = ?, photo_count = ?, last_updated = ?
        WHERE id = ?
        ''', (new_level, photo_count, timestamp, zone_id))
    else:
        # Create new zone
        cursor.execute('''
        INSERT INTO zones (center_lat, center_lng, radius, waste_level, photo_count, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (latitude, longitude, radius, int(severity_score), 1, timestamp))
    
    conn.commit()
    conn.close()

def get_all_zones():
    """Get all waste zones"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, center_lat, center_lng, radius, waste_level, photo_count, last_updated
    FROM zones
    ORDER BY waste_level DESC
    ''')
    
    zones = []
    for row in cursor.fetchall():
        zones.append({
            'id': row['id'],
            'center_lat': row['center_lat'],
            'center_lng': row['center_lng'],
            'radius': row['radius'],
            'waste_level': row['waste_level'],
            'photo_count': row['photo_count'],
            'last_updated': row['last_updated']
        })
    
    conn.close()
    return zones

def get_zone_by_location(latitude, longitude, radius=0.005):
    """Get a zone by geographic location"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, center_lat, center_lng, radius, waste_level, photo_count, last_updated
    FROM zones
    WHERE ABS(center_lat - ?) < ? AND ABS(center_lng - ?) < ?
    ''', (latitude, radius, longitude, radius))
    
    row = cursor.fetchone()
    if row:
        zone = {
            'id': row['id'],
            'center_lat': row['center_lat'],
            'center_lng': row['center_lng'],
            'radius': row['radius'],
            'waste_level': row['waste_level'],
            'photo_count': row['photo_count'],
            'last_updated': row['last_updated']
        }
        conn.close()
        return zone
    
    conn.close()
    return None

def create_demo_data():
    """Create sample data for demonstration"""
    # This would be implemented for the demo
    pass