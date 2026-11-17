"""
Interview Questions Seeder

Seeds interview practice questions from CSV file.
"""
import csv
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import InterviewQuestionModel, ProfessionModel
from utils.logger import get_logger

logger = get_logger("seeds.interview_questions")

# Mapping for profession names in CSV that are the same but have different titles
PROFESSION_MAPPING = {
    "Tech / Product": "Technology",
    "MBA / Leadership": "MBA / Executive",
    "Energy": "Energy & Sustainability"
}

def seed_interview_questions(db: Session) -> dict:
    """
    Seed interview practice questions from CSV file.
    
    Reads from interview_questions_clean.csv and populates the interview_questions table.
    Maps profession names from CSV to profession IDs in the database.
    Skips records where profession is not found.
    
    Args:
        db: Database session
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Check if interview questions already exist - skip seeding if so
        existing_count = db.query(InterviewQuestionModel).count()
        if existing_count > 0:
            message = f"Interview questions already seeded ({existing_count} questions exist). Skipping."
            logger.info(message)
            return {
                "success": True,
                "message": message,
                "created": 0,
                "skipped": existing_count
            }
        
        # Get the CSV file path - using new clean CSV
        csv_path = Path(__file__).parent / "interview_questions_clean.csv"
        
        if not csv_path.exists():
            error_msg = f"CSV file not found: {csv_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "created": 0,
                "skipped": 0
            }
        
        # Cache profession lookups for efficiency
        profession_cache = {}
        professions = db.query(ProfessionModel).all()
        for profession in professions:
            profession_cache[profession.name] = profession.Id
        
        logger.info(f"Loaded {len(profession_cache)} professions: {list(profession_cache.keys())}")
        
        # Prepare batch of questions to insert
        questions_to_insert = []
        skipped_count = 0
        profession_not_found_count = 0
        unmapped_professions = set()
        duplicate_count = 0
        seen_keys = set()  # Track duplicates within CSV
        
        logger.info("Reading CSV and preparing questions...")
        
        # Read and process CSV file
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                try:
                    # Get profession name from CSV and apply mapping if needed
                    profession_name = row.get('profession', '').strip()
                    mapped_profession = PROFESSION_MAPPING.get(profession_name, profession_name)
                    
                    # Look up profession ID
                    profession_id = profession_cache.get(mapped_profession)
                    
                    if not profession_id:
                        if profession_name not in unmapped_professions:
                            logger.warning(f"Profession '{profession_name}' (mapped to '{mapped_profession}') not found in database")
                            unmapped_professions.add(profession_name)
                        profession_not_found_count += 1
                        skipped_count += 1
                        continue
                    
                    # Prepare question data with all new fields
                    question_text = row.get('question', '').strip()
                    category = row.get('category', '').strip() or None
                    
                    # Check for duplicates within CSV using unique constraint fields
                    unique_key = (question_text, str(profession_id), category)
                    if unique_key in seen_keys:
                        duplicate_count += 1
                        skipped_count += 1
                        continue
                    seen_keys.add(unique_key)
                    
                    question_data = {
                        "question_text": question_text,
                        "category": category,
                        "difficulty": row.get('difficulty', '').strip() or None,
                        "framework": row.get('framework', '').strip() or None,
                        "skills_tested": row.get('skills_tested', '').strip() or None,
                        "framework_description": row.get('framework_description', '').strip() or None,
                        "good_answer_criteria": row.get('good_answer_criteria', '').strip() or None,
                        "listening_guideline": row.get('listening_guidelines', '').strip() or None,
                        "common_issues": row.get('common_issues', '').strip() or None,
                        "notes": row.get('notes', '').strip() or None,
                        "profession_id": profession_id
                    }
                    
                    # Handle time_limit (convert to integer)
                    time_limit_str = row.get('time_limit', '').strip()
                    if time_limit_str:
                        try:
                            question_data["time_limit"] = int(time_limit_str)
                        except ValueError:
                            logger.warning(f"Row {row_num}: Invalid time_limit '{time_limit_str}', setting to None")
                            question_data["time_limit"] = None
                    else:
                        question_data["time_limit"] = None
                    
                    # Create question object and add to batch
                    new_question = InterviewQuestionModel(**question_data)
                    questions_to_insert.append(new_question)
                    
                    # Log progress every 500 rows
                    if len(questions_to_insert) % 500 == 0:
                        logger.info(f"Progress: Prepared {len(questions_to_insert)} questions...")
                    
                except Exception as row_error:
                    logger.error(f"Row {row_num}: Error processing row - {str(row_error)}")
                    skipped_count += 1
                    continue
        
        # Bulk insert all questions in one transaction
        if questions_to_insert:
            logger.info(f"Inserting {len(questions_to_insert)} questions into database...")
            try:
                db.bulk_save_objects(questions_to_insert)
                db.commit()
                created_count = len(questions_to_insert)
                logger.info(f"✓ Successfully inserted {created_count} questions")
            except IntegrityError as e:
                db.rollback()
                logger.error(f"Bulk insert failed with IntegrityError. Falling back to individual inserts...")
                logger.error(f"Error: {str(e)}")
                
                # Fallback: Insert one by one to skip duplicates
                created_count = 0
                for question in questions_to_insert:
                    try:
                        db.add(question)
                        db.commit()
                        created_count += 1
                    except IntegrityError:
                        db.rollback()
                        duplicate_count += 1
                        continue
                
                logger.info(f"✓ Inserted {created_count} questions individually (skipped {duplicate_count} duplicates)")
        else:
            created_count = 0
            logger.warning("No questions to insert")
        
        # Report unmapped professions if any
        if unmapped_professions:
            logger.warning(f"Unmapped professions found in CSV: {', '.join(unmapped_professions)}")
        
        if duplicate_count > 0:
            logger.info(f"Skipped {duplicate_count} duplicate questions")
        
        message = (f"Interview questions seeded successfully. "
                  f"Created: {created_count}, Skipped: {skipped_count} "
                  f"(Profession not found: {profession_not_found_count}, Duplicates: {duplicate_count})")
        logger.info(message)
        
        return {
            "success": True,
            "message": message,
            "created": created_count,
            "skipped": skipped_count,
            "profession_not_found": profession_not_found_count,
            "duplicates": duplicate_count,
            "unmapped_professions": list(unmapped_professions)
        }
        
    except Exception as e:
        logger.error(f"Error seeding interview questions: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "created": 0,
            "skipped": 0
        }
