from database import SessionLocal
from models import BugPattern


def find_matching_pattern(error_text):
    db = SessionLocal()

    patterns = db.query(BugPattern).all()

    matches = []

    for pattern in patterns:
        if pattern.error_type.lower() in error_text.lower():
            matches.append(pattern)

    db.close()

    return matches