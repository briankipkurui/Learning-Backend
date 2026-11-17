"""
Main Seeder Script

Orchestrates all database seeding operations.
Run this script to seed your database with initial data.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.database import SessionLocal
from seeds.course_status_seeder import seed_course_statuses
from seeds.content_type_seeder import seed_lesson_content_types
from seeds.job_activity_type_seeder import seed_job_activity_types
from seeds.age_groups_seeder import seed_age_groups
from seeds.professions_seeder import seed_professions
from seeds.interview_questions_seeder import seed_interview_questions
from seeds.policies_seeder import seed_policies
from utils.logger import get_logger

logger = get_logger("seeds.main")

def run_seeds():
    """
    Run all database seeders
    """
    db = SessionLocal()
    
    try:
        logger.info("🌱 Starting database seeding...")
        
        # Track overall results
        total_results = {
            "success": True,
            "seeders_run": 0,
            "seeders_failed": 0,
            "details": []
        }
        
        # Course Status Seeder
        logger.info("📋 Seeding course statuses...")
        course_status_result = seed_course_statuses(db)
        total_results["seeders_run"] += 1
        total_results["details"].append({
            "seeder": "Course Statuses",
            "result": course_status_result
        })
        
        if not course_status_result["success"]:
            total_results["success"] = False
            total_results["seeders_failed"] += 1
            logger.error(f"❌ Course status seeding failed: {course_status_result['message']}")
        else:
            logger.info(f"✅ {course_status_result['message']}")

        # Lesson Content Type Seeder
        logger.info("📋 Seeding lesson content types...")
        content_type_result = seed_lesson_content_types(db)
        total_results["seeders_run"] += 1

        total_results["details"].append({
            "seeder": "Lesson Content Types",
            "result": content_type_result
        })

        if not content_type_result["success"]:
            total_results["success"] = False
            total_results["seeders_failed"] += 1
            logger.error(f"❌ Lesson content type seeding failed: {content_type_result['message']}")
        else:
            logger.info(f"✅ {content_type_result['message']}")

        # Job Activity Type Seeder
        logger.info("📋 Seeding job activity types...")
        job_activity_result = seed_job_activity_types(db)
        total_results["seeders_run"] += 1
        total_results["details"].append({
            "seeder": "Job Activity Types",
            "result": job_activity_result
        })

        if not job_activity_result["success"]:
            total_results["success"] = False
            total_results["seeders_failed"] += 1
            logger.error(f"❌ Job activity type seeding failed: {job_activity_result['message']}")
        else:
            logger.info(f"✅ {job_activity_result['message']}")

        # Age Groups Seeder
        logger.info("📋 Seeding age groups...")
        age_group_result = seed_age_groups(db)
        total_results["seeders_run"] += 1
        total_results["details"].append({
            "seeder": "Age Groups",
            "result": age_group_result
        })

        if not age_group_result["success"]:
            total_results["success"] = False
            total_results["seeders_failed"] += 1
            logger.error(f"❌ Age group seeding failed: {age_group_result['message']}")
        else:
            logger.info(f"✅ {age_group_result['message']}")

        # Professions Seeder
        logger.info("📋 Seeding professions...")
        professions_result = seed_professions(db)
        total_results["seeders_run"] += 1
        total_results["details"].append({
            "seeder": "Professions",
            "result": professions_result
        })

        if not professions_result["success"]:
            total_results["success"] = False
            total_results["seeders_failed"] += 1
            logger.error(f"❌ Professions seeding failed: {professions_result['message']}")
        else:
            logger.info(f"✅ {professions_result['message']}")

        # Interview Questions Seeder (must run after professions)
        logger.info("📋 Seeding interview practice questions...")
        interview_questions_result = seed_interview_questions(db)
        total_results["seeders_run"] += 1
        total_results["details"].append({
            "seeder": "Interview Questions",
            "result": interview_questions_result
        })

        if not interview_questions_result["success"]:
            total_results["success"] = False
            total_results["seeders_failed"] += 1
            logger.error(f"❌ Interview questions seeding failed: {interview_questions_result['message']}")
        else:
            logger.info(f"✅ {interview_questions_result['message']}")

        # Policies Seeder
        logger.info("📋 Seeding policies...")
        policies_result = seed_policies(db)
        total_results["seeders_run"] += 1
        total_results["details"].append({
            "seeder": "Policies",
            "result": policies_result
        })

        if not policies_result["success"]:
            total_results["success"] = False
            total_results["seeders_failed"] += 1
            logger.error(f"❌ Policies seeding failed: {policies_result['message']}")
        else:
            logger.info(f"✅ {policies_result['message']}")

        # Add more seeders here as you create them
        # Summary
        if total_results["success"]:
            logger.info(f"🎉 Database seeding completed successfully!")
        else:
            logger.error(f"❌ Database seeding completed with errors!")
        
        return total_results
        
    except Exception as e:
        logger.error(f"❌ Fatal error during seeding: {str(e)}")
        return {
            "success": False,
            "message": f"Fatal error: {str(e)}",
            "seeders_run": 0,
            "seeders_failed": 1
        }
    finally:
        db.close()

if __name__ == "__main__":
    """
    Run the seeder script directly
    
    Usage:
        python seeds/seed.py
    """
    results = run_seeds()
    
    # Exit with appropriate code
    exit_code = 0 if results["success"] else 1
    sys.exit(exit_code)