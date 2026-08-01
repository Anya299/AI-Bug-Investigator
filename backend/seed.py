import json
from database import SessionLocal
from models import KnowledgeEntry


db = SessionLocal()

try:
    with open("seed_data.json", "r") as file:
        bugs = json.load(file)

    for bug in bugs:
        record = KnowledgeEntry(
            type="bug_fix",
            error_type=...,
            error_message=...,
            language=...,
            framework=...,
            root_cause=...,
            common_fix=...,
            tags=...,
            success_rate=0.0,
            is_verified=True
        )
        db.add(record)

    db.commit()

    print(f"Inserted {len(bugs)} bug records successfully")

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()