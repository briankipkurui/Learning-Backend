from sqlalchemy.orm import Session
from models import ProfessionModel
from utils.logger import get_logger

logger = get_logger("seeds.professions")

def seed_professions(db: Session) -> dict:
    """
    Seed professions for interview practice.
    
    Args:
        db: Database session
        
    Returns:
        dict: Result with success status and message
    """
    try:
        professions = [
            {
                "name": "Finance",
                "description": "Financial services, investment banking, private equity, and related fields"
            },
            {
                "name": "Consulting",
                "description": "Management consulting, strategy consulting, and advisory services"
            },
            {
                "name": "Technology",
                "description": "Software engineering, product management, data science, and tech roles"
            },
            {
                "name": "Energy & Sustainability",
                "description": "Renewable energy, sustainability consulting, environmental services"
            },
            {
                "name": "Operations",
                "description": "Operations management, supply chain, logistics, and process improvement"
            },
            {
                "name": "MBA / Executive",
                "description": "Executive-level and MBA graduate positions across industries"
            },
            {
                "name": "Business Operations",
                "description": "Business operations strategy, process optimization, and operational excellence"
            }
        ]
        
        created_count = 0
        skipped_count = 0
        
        for profession_data in professions:
            # Check if profession already exists (by name)
            existing_profession = db.query(ProfessionModel).filter(
                ProfessionModel.name == profession_data["name"]
            ).first()
            
            if existing_profession:
                logger.info(f"Profession '{profession_data['name']}' already exists, skipping")
                skipped_count += 1
                continue
                
            # Create new profession
            new_profession = ProfessionModel(**profession_data)
            db.add(new_profession)
            created_count += 1
            logger.info(f"Created profession: {profession_data['name']}")
        
        # Commit all changes
        db.commit()
        
        message = f"Professions seeded successfully. Created: {created_count}, Skipped: {skipped_count}"
        logger.info(message)
        
        return {
            "success": True,
            "message": message,
            "created": created_count,
            "skipped": skipped_count
        }
    except Exception as e:
        logger.error(f"Error seeding professions: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "created": 0,
            "skipped": 0
        }
