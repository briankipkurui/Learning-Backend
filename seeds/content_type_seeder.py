"""
Course content type seeder

Seeds the content_types table with predefined content types.
"""

from sqlalchemy.orm import Session
from models import LessonContentType
from utils.logger import get_logger

logger = get_logger("seeds.content_type")

def seed_lesson_content_types(db: Session) -> dict:
    """
    Seed lesson content types: VIDEO, ARTICLE, QUIZ
    
    Args:
        db: Database session
        
    Returns:
        dict: Result with success status and message
    """
    try:
        content_types = [
            {"name": "Video"},
            {"name": "Article"}, 
            {"name": "Quiz"}
        ]
        
        created_count = 0
        skipped_count = 0
        
        for ct_data in content_types:
            # Check if content type already exists
            existing_ct = db.query(LessonContentType).filter(
                LessonContentType.name == ct_data["name"]
            ).first()
            
            if existing_ct:
                logger.info(f"Content type '{ct_data['name']}' already exists, skipping")
                skipped_count += 1
                continue
                
            # Create new content type
            new_ct = LessonContentType(**ct_data)
            db.add(new_ct)
            created_count += 1
            logger.info(f"Created content type: {ct_data['name']}")
        
        # Commit all changes
        db.commit()
        
        message = f"Lesson content types seeded successfully. Created: {created_count}, Skipped: {skipped_count}"
        logger.info(message)
        
        return {
            "success": True,
            "message": message,
            "created": created_count,
            "skipped": skipped_count
        }
        
    except Exception as e:
        logger.error(f"Error seeding lesson content types: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }