import json
from database import SessionLocal
from models import BugKnowledgeBase


db = SessionLocal()

try:
    with open("seed_data.json", "r") as file:
        bugs = json.load(file)

    for bug in bugs:
        record = BugKnowledgeBase(
            title=bug["title"],
            language=bug["language"],
            framework=bug["framework"],
            error_pattern=bug["error_pattern"],
            root_cause=bug["root_cause"],
            solution=bug["solution"]
        )

        db.add(record)

    db.commit()

    print(f"Inserted {len(bugs)} bug records successfully")

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()