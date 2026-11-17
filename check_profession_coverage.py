"""
Check which professions have no interview questions in the database
"""
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models.database import get_database
from models.user import ProfessionModel
from models.job_applications import InterviewQuestionModel

def check_profession_coverage():
    """Check which professions are not represented in interview questions"""
    db = next(get_database())
    
    try:
        print("=" * 80)
        print("PROFESSION COVERAGE IN INTERVIEW QUESTIONS")
        print("=" * 80)
        
        # Get all professions
        all_professions = db.query(ProfessionModel).all()
        total_professions = len(all_professions)
        
        # Get professions with interview questions
        professions_with_questions = db.query(
            ProfessionModel.Id,
            ProfessionModel.name,
            func.count(InterviewQuestionModel.Id).label('question_count')
        ).outerjoin(
            InterviewQuestionModel, 
            ProfessionModel.Id == InterviewQuestionModel.profession_id
        ).group_by(
            ProfessionModel.Id,
            ProfessionModel.name
        ).order_by(
            func.count(InterviewQuestionModel.Id).desc()
        ).all()
        
        professions_with_data = [p for p in professions_with_questions if p.question_count > 0]
        professions_without_data = [p for p in professions_with_questions if p.question_count == 0]
        
        print(f"\nTotal professions in database: {total_professions}")
        print(f"Professions with interview questions: {len(professions_with_data)}")
        print(f"Professions WITHOUT interview questions: {len(professions_without_data)}")
        
        if professions_with_data:
            print("\n" + "=" * 80)
            print("PROFESSIONS WITH INTERVIEW QUESTIONS:")
            print("=" * 80)
            for prof in professions_with_data:
                print(f"✓ {prof.name}: {prof.question_count} questions")
        
        if professions_without_data:
            print("\n" + "=" * 80)
            print("PROFESSIONS WITHOUT INTERVIEW QUESTIONS:")
            print("=" * 80)
            for prof in professions_without_data:
                print(f"✗ {prof.name}: NO QUESTIONS")
        
        print("\n" + "=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    check_profession_coverage()
