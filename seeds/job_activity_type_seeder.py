from sqlalchemy.orm import Session
from models import ActivityTypeModel
from utils.logger import get_logger

logger = get_logger("seeds.job_activity_type")

def seed_job_activity_types(db: Session) -> dict:
    """
    Seed job activity types: APPLIED, INTERVIEWED, OFFERED, REJECTED
    
    Args:
        db: Database session
        
    Returns:
        dict: Result with success status and message
    """
    try:
        activity_types = [
            {"name": "APPLICATION SUBMITTED"},
            {"name": "APPLICATION VIEWED"},
            {"name": "HR SCREENING CALL"},
            {"name": "PHONE SCREEN"},
            {"name": "TECHNICAL ASSESSMENT"},
            {"name": "TECHNICAL INTERVIEW"},
            {"name": "BEHAVIORAL INTERVIEW"},
            {"name": "HIRING MANAGER INTERVIEW"},
            {"name": "PANEL INTERVIEW"},
            {"name": "ONSITE INTERVIEW"},
            {"name": "FINAL ROUND"},
            {"name": "REFERENCE CHECK"},
            {"name": "BACKGROUND CHECK"},
            {"name": "OFFER RECEIVED"},
            {"name": "OFFER ACCEPTED"},
            {"name": "OFFER DECLINED"},
            {"name": "REJECTED"},
            {"name": "WITHDREW APPLICATION"},
            {"name": "FOLLOW UP EMAIL SENT"},
            {"name": "FOLLOW UP CALL"},
            {"name": "THANK YOU NOTE SENT"},
            {"name": "NEGOTIATION"},
            {"name": "WAITING FOR RESPONSE"},
            {"name": "OTHER"}
        ]
        
        created_count = 0
        skipped_count = 0
        
        for activity_data in activity_types:
            # Check if activity type already exists
            existing_activity = db.query(ActivityTypeModel).filter(
                ActivityTypeModel.name == activity_data["name"]
            ).first()
            
            if existing_activity:
                logger.info(f"Activity type '{activity_data['name']}' already exists, skipping")
                skipped_count += 1
                continue
                
            # Create new activity type
            new_activity = ActivityTypeModel(**activity_data)
            db.add(new_activity)
            created_count += 1
            logger.info(f"Created activity type: {activity_data['name']}")
        
        # Commit all changes
        db.commit()
        
        message = f"Job activity types seeded successfully. Created: {created_count}, Skipped: {skipped_count}"
        logger.info(message)
        
        return {
            "success": True,
            "message": message,
            "created": created_count,
            "skipped": skipped_count
        }
    except Exception as e:
        logger.error(f"Error seeding job activity types: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }