# Database Seeding System

This directory contains database seeding scripts to populate your database with initial/default data.

## 🚀 Quick Start

### Run All Seeders
```bash
# From project root
python seed_db.py

# Or directly
python seeds/seed.py
```

### Run with Virtual Environment
```bash
# Activate virtual environment first
source .venv/Scripts/activate  # Windows
source .venv/bin/activate      # Linux/Mac

# Then run seeder
python seed_db.py
```

## 📁 Structure

```
seeds/
├── __init__.py                 # Package initialization
├── seed.py                     # Main orchestrator script
├── course_status_seeder.py     # Course status seeder
└── README.md                   # This file
```

## 🌱 Available Seeders

### Course Status Seeder
- **File**: `course_status_seeder.py`
- **Purpose**: Seeds the `course_statuses` table
- **Data**: DRAFT, PUBLISHED, ARCHIVED
- **Safe**: Won't duplicate existing records

### Lesson Content Type Seeder
- **File**: `content_type_seeder.py`
- **Purpose**: Seeds the `lesson_content_types` table
- **Safe**: Won't duplicate existing records

### Job Activity Type Seeder
- **File**: `job_activity_type_seeder.py`
- **Purpose**: Seeds the `activity_types` table
- **Data**: Application tracking activity types
- **Safe**: Won't duplicate existing records

### Age Groups Seeder
- **File**: `age_groups_seeder.py`
- **Purpose**: Seeds the `age_groups` table
- **Safe**: Won't duplicate existing records

### Credit Packages Seeder
- **File**: `credit_packages_seeder.py`
- **Purpose**: Seeds CV analysis packages
- **Safe**: Won't duplicate existing records

### Interview Packages Seeder
- **File**: `interview_packages_seeder.py`
- **Purpose**: Seeds interview practice packages
- **Safe**: Won't duplicate existing records

### Professions Seeder
- **File**: `professions_seeder.py`
- **Purpose**: Seeds the `professions` table
- **Data**: Finance, Consulting, Technology, Energy & Sustainability, Operations, MBA / Executive
- **Safe**: Won't duplicate existing records
- **Note**: Must run before Interview Questions Seeder

### Interview Questions Seeder
- **File**: `interview_questions_seeder.py`
- **Purpose**: Seeds interview practice questions from CSV
- **Source**: `InterviewPractice.csv`
- **Dependencies**: Requires professions to be seeded first
- **Data Mapping**:
  - `category` → `category`
  - `question` → `question_text`
  - `profession` → `profession_id` (looked up from professions table)
  - `framework` → `framework`
  - `skills_tested` → `skills_tested`
  - `difficulty` → `difficulty`
  - `notes` → `notes`
  - `time_limit` → `time_limit`
- **Safe**: Won't duplicate existing questions (checks by question_text + profession_id)
- **Behavior**: Skips records where profession is not found in database

## 🔧 Adding New Seeders

### 1. Create Seeder File
```python
# seeds/your_new_seeder.py
from sqlalchemy.orm import Session
from models import YourModel
from utils.logger import get_logger

logger = get_logger("seeds.your_seeder")

def seed_your_data(db: Session) -> dict:
    try:
        # Your seeding logic here
        
        return {
            "success": True,
            "message": "Success message",
            "created": created_count,
            "skipped": skipped_count
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "created": 0,
            "skipped": 0
        }
```

### 2. Register in Main Seeder
Add your seeder to `seeds/seed.py`:

```python
# Import your seeder
from seeds.your_new_seeder import seed_your_data

# Add to run_seeds() function
logger.info("🔧 Seeding your data...")
your_result = seed_your_data(db)
total_results["seeders_run"] += 1
total_results["details"].append({
    "seeder": "Your Data",
    "result": your_result
})
```

## 📊 Output Format

Seeders return a standardized format:
```python
{
    "success": bool,           # Whether seeding succeeded
    "message": str,            # Human-readable message
    "created": int,            # Number of records created
    "skipped": int            # Number of records skipped (already exist)
}
```

## 🛡️ Safety Features

- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Transaction Safe**: Rollback on errors
- ✅ **Duplicate Protection**: Won't create duplicates
- ✅ **Detailed Logging**: Comprehensive logging output
- ✅ **Error Handling**: Graceful error handling

## 🎯 Best Practices

1. **Check for Existing Records**: Always check if data already exists
2. **Use Transactions**: Wrap operations in try/catch with rollback
3. **Log Everything**: Use the logger for detailed output
4. **Return Standard Format**: Follow the result format convention
5. **Make it Idempotent**: Safe to run multiple times

## 🚨 Important Notes

- Always activate your virtual environment before running
- Ensure your database is migrated before seeding
- Review the logs for any warnings or errors
- Seeders are designed to be safe and won't overwrite existing data

## 📝 Example Usage

```bash
$ python seed_db.py

🌱 Career Elevate Database Seeder
========================================
🌱 Starting database seeding...
📋 Seeding course statuses...
✅ Course statuses seeded successfully. Created: 3, Skipped: 0
🎉 Database seeding completed successfully!
📊 Summary: 1 seeders run, 0 failed

============================================================
📋 SEEDING RESULTS
============================================================

Course Statuses: ✅ SUCCESS
  Message: Course statuses seeded successfully. Created: 3, Skipped: 0
  Created: 3, Skipped: 0

============================================================

🏁 Seeding completed with exit code: 0
```