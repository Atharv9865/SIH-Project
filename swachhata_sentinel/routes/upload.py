from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import os
import uuid
from datetime import datetime

from models.database import get_db, Photo, Zone
from models.schemas import PhotoCreate, PhotoResponse
from ml.image_classifier import PollutionDetector
from ml.zone_mapper import ZoneMapper

router = APIRouter()
pollution_detector = PollutionDetector()
zone_mapper = ZoneMapper()

@router.post("/photo", response_model=PhotoResponse)
async def upload_photo(
    file: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload a photo with geolocation data
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join("uploads", unique_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Create database entry
    db_photo = Photo(
        user_id=user_id,
        image_path=file_path,
        latitude=latitude,
        longitude=longitude,
        timestamp=datetime.utcnow(),
        verified_status="pending"
    )
    
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    
    # Analyze the image (in a real app, this might be done asynchronously)
    analysis_result = pollution_detector.predict(file_path)
    
    # Return the created photo
    return db_photo

@router.post("/api/upload-photo")
async def api_upload_photo(
    file: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    API endpoint for uploading a photo with geolocation data
    Returns upload status and zone impact
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join("uploads", unique_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Create database entry
    db_photo = Photo(
        user_id=user_id,
        image_path=file_path,
        latitude=latitude,
        longitude=longitude,
        timestamp=datetime.utcnow(),
        verified_status="pending"
    )
    
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    
    # Analyze the image
    analysis_result = pollution_detector.predict(file_path)
    
    # Get all photos to assess zone impact
    all_photos = db.query(Photo).filter(Photo.verified_status != "rejected").all()
    photo_list = [
        {
            "latitude": p.latitude,
            "longitude": p.longitude,
            "user_id": p.user_id,
            "timestamp": p.timestamp
        } for p in all_photos
    ]
    
    # Use ZoneMapper to assess impact
    zone_impact = zone_mapper.update_zones(photo_list)
    
    # Find which zone this photo belongs to
    photo_zone = None
    for label, cluster in zone_impact['clusters'].items():
        if label in zone_impact['zone_scores'] and label in zone_impact['zone_types']:
            photo_zone = {
                "zone_id": label,
                "zone_type": zone_impact['zone_types'][label],
                "pollution_score": zone_impact['zone_scores'][label]
            }
            break
    
    return {
        "upload_status": "success",
        "photo_id": db_photo.photo_id,
        "zone_impact": photo_zone
    }

@router.get("/photos", response_model=list[PhotoResponse])
def get_photos(
    user_id: Optional[int] = None,
    verified_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get photos with optional filtering
    """
    query = db.query(Photo)
    
    if user_id:
        query = query.filter(Photo.user_id == user_id)
    
    if verified_status:
        query = query.filter(Photo.verified_status == verified_status)
    
    photos = query.all()
    return photos

@router.put("/photos/{photo_id}/verify")
def verify_photo(
    photo_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update verification status of a photo
    """
    if status not in ["verified", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'verified' or 'rejected'")
    
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    photo.verified_status = status
    db.commit()
    
    return {"message": f"Photo {photo_id} marked as {status}"}