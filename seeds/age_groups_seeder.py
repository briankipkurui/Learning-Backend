from sqlalchemy.orm import Session
from models import AgeGroupModel
from utils.logger import get_logger

logger = get_logger("seeds.age_group")

def seed_age_groups(db: Session) -> dict:
    """
    Seed age groups into the database.
    
    Args:
        db: Database session
        
    Returns:
        dict: Result with success status and message
    """
    try:
        age_groups = [
            {"name": "Below 20", "min_age": 0, "max_age": 19, "sort_order": 1},
            {"name": "20-24", "min_age": 20, "max_age": 24, "sort_order": 2},
            {"name": "25-29", "min_age": 25, "max_age": 29, "sort_order": 3},
            {"name": "30-34", "min_age": 30, "max_age": 34, "sort_order": 4},
            {"name": "35-39", "min_age": 35, "max_age": 39, "sort_order": 5},
            {"name": "40-44", "min_age": 40, "max_age": 44, "sort_order": 6},
            {"name": "45-49", "min_age": 45, "max_age": 49, "sort_order": 7},
            {"name": "50-54", "min_age": 50, "max_age": 54, "sort_order": 8},
            {"name": "55-59", "min_age": 55, "max_age": 59, "sort_order": 9},
            {"name": "60-64", "min_age": 60, "max_age": 64, "sort_order": 10},
            {"name": "65+", "min_age": 65, "max_age": 999, "sort_order": 11}
        ]
        
        created_count = 0
        skipped_count = 0
        
        for age_group_data in age_groups:
            # Check if age group already exists
            existing_group = db.query(AgeGroupModel).filter(
                AgeGroupModel.name == age_group_data["name"]
            ).first()
            
            if existing_group:
                logger.info(f"Age group '{age_group_data['name']}' already exists, skipping")
                skipped_count += 1
                continue
                
            # Create new age group
            new_group = AgeGroupModel(**age_group_data)
            db.add(new_group)
            created_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Seeding completed: {created_count} created, {skipped_count} skipped."
        }
        
    except Exception as e:
        logger.error(f"Error seeding age groups: {e}")
        return {
            "success": False,
            "message": f"Error occurred: {e}"
        }