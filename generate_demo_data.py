"""
Demo Data Generator for Swachhata Sentinel
Creates realistic waste report data across a city for demonstration purposes
"""

import sqlite3
import random
import datetime
import os
import shutil
import sqlite3
from database import init_db, DB_PATH

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Configuration
NUM_PHOTOS = 50  # Number of demo photos to generate
CITY_CENTER = (18.5204, 73.8567)  # Pune city center (latitude, longitude)
CITY_RADIUS = 0.05  # Approximate radius in degrees (~5km)
WASTE_TYPES = ["plastic", "paper", "metal", "organic", "glass", "mixed"]
SEVERITY_RANGES = {
    "red": (7, 10),
    "orange": (5, 7),
    "yellow": (3, 5),
    "green": (1, 3)
}

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Sample images directory (you'll need to add some sample waste images here)
SAMPLE_IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'demo_images')
os.makedirs(SAMPLE_IMAGES_DIR, exist_ok=True)

def generate_location(center, radius, zone_type=None):
    """Generate a random location within radius of center, with bias based on zone type"""
    # Different zone types are more likely in different areas
    # Red zones near markets, yellow/orange in residential, green in parks
    
    # Base random offset
    angle = random.uniform(0, 2 * 3.14159)
    
    # Adjust radius based on zone type to create natural patterns
    if zone_type == "red":
        # Red zones clustered more tightly
        distance = random.uniform(0, radius * 0.4)
    elif zone_type == "orange":
        # Orange zones in middle distance
        distance = random.uniform(radius * 0.3, radius * 0.6)
    elif zone_type == "yellow":
        # Yellow zones spread out
        distance = random.uniform(radius * 0.5, radius * 0.8)
    elif zone_type == "green":
        # Green zones at the periphery
        distance = random.uniform(radius * 0.7, radius)
    else:
        # Random distribution
        distance = random.uniform(0, radius)
    
    # Calculate new point
    lat = center[0] + distance * math.cos(angle)
    lng = center[1] + distance * math.sin(angle)
    
    return (lat, lng)

def generate_timestamp(days_ago=30):
    """Generate a random timestamp within the last X days"""
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=random.uniform(0, days_ago))
    return (now - delta).isoformat()

def copy_sample_image(filename):
    """Copy a sample image to the uploads directory with a new filename"""
    # Get list of sample images
    sample_images = [f for f in os.listdir(SAMPLE_IMAGES_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if not sample_images:
        # If no sample images, create a placeholder text file
        print("No sample images found in demo_images directory. Please add some images.")
        with open(os.path.join(UPLOAD_DIR, filename), 'w') as f:
            f.write("Placeholder for demo image")
        return filename
    
    # Select a random sample image
    sample_image = random.choice(sample_images)
    source_path = os.path.join(SAMPLE_IMAGES_DIR, sample_image)
    dest_path = os.path.join(UPLOAD_DIR, filename)
    
    # Copy the image
    shutil.copy(source_path, dest_path)
    return filename

def generate_demo_data():
    """Generate demo data and insert into database"""
    # Initialize database
    init_db()
    conn = get_db_connection()
    
    # Clear existing data
    conn.execute('DELETE FROM photos')
    conn.execute('DELETE FROM zones')
    conn.commit()
    
    # Generate photos with natural distribution of zone types
    zone_distribution = {
        "red": int(NUM_PHOTOS * 0.2),      # 20% red zones
        "orange": int(NUM_PHOTOS * 0.3),   # 30% orange zones
        "yellow": int(NUM_PHOTOS * 0.3),   # 30% yellow zones
        "green": int(NUM_PHOTOS * 0.2)     # 20% green zones
    }
    
    photos_added = 0
    
    # Add photos for each zone type
    for zone_type, count in zone_distribution.items():
        for i in range(count):
            # Generate location based on zone type
            lat, lng = generate_location(CITY_CENTER, CITY_RADIUS, zone_type)
            
            # Generate severity score based on zone type
            severity_min, severity_max = SEVERITY_RANGES[zone_type]
            severity_score = round(random.uniform(severity_min, severity_max), 1)
            
            # Generate waste type with some correlation to severity
            if severity_score > 7:
                # Higher severity more likely to be mixed waste
                waste_type = random.choice(["mixed"] * 3 + WASTE_TYPES)
            else:
                waste_type = random.choice(WASTE_TYPES)
            
            # Generate confidence level
            confidence = random.uniform(0.7, 0.98)
            
            # Generate timestamp with some recency bias
            if zone_type == "red":
                # Red zones tend to have more recent reports
                timestamp = generate_timestamp(days_ago=10)
            else:
                timestamp = generate_timestamp(days_ago=30)
            
            # Generate unique filename
            filename = f"demo_{zone_type}_{i+1}.jpg"
            image_path = copy_sample_image(filename)
            
            # Insert into database
            conn.execute(
                'INSERT INTO photos (image_path, latitude, longitude, timestamp, user_id, pollution_category, severity_score, pollution_confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (image_path, lat, lng, timestamp, random.randint(1, 10), waste_type, severity_score, confidence)
            )
            
            photos_added += 1
            print(f"Added photo {photos_added}/{NUM_PHOTOS}: {zone_type} zone with {waste_type} waste")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"Successfully generated {photos_added} demo photos")
    print("Please run the application and navigate to the map page to see the demo data")

if __name__ == "__main__":
    import math  # Import here to avoid issues if this module is imported elsewhere
    generate_demo_data()