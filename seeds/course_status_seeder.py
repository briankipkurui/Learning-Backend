"""
Course Status Seeder

Seeds the course_statuses table with predefined status values.
"""
from sqlalchemy.orm import Session
from models import CourseStatusLookup
from utils.logger import get_logger

logger = get_logger("seeds.course_status")

def seed_course_statuses(db: Session) -> dict:
    """
    Seed course statuses: DRAFT, PUBLISHED, ARCHIVED
    
    Args:
        db: Database session
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Define course statuses to seed
        statuses = [
            {"name": "DRAFT"},
            {"name": "PUBLISHED"}, 
            {"name": "ARCHIVED"}
        ]
        
        created_count = 0
        skipped_count = 0
        
        for status_data in statuses:
            # Check if status already exists
            existing_status = db.query(CourseStatusLookup).filter(
                CourseStatusLookup.name == status_data["name"]
            ).first()
            
            if existing_status:
                logger.info(f"Course status '{status_data['name']}' already exists, skipping")
                skipped_count += 1
                continue
                
            # Create new status
            new_status = CourseStatusLookup(**status_data)
            db.add(new_status)
            created_count += 1
            logger.info(f"Created course status: {status_data['name']}")
        
        # Commit all changes
        db.commit()
        
        message = f"Course statuses seeded successfully. Created: {created_count}, Skipped: {skipped_count}"
        logger.info(message)
        
        return {
            "success": True,
            "message": message,
            "created": created_count,
            "skipped": skipped_count
        }
        
    except Exception as e:
        db.rollback()
        error_msg = f"Error seeding course statuses: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "created": 0,
            "skipped": 0
        }