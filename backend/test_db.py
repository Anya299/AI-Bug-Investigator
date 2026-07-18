from database import SessionLocal
from models import BugReport

db = SessionLocal()

bugs = db.query(BugReport).all()

print("Total bugs:", len(bugs))

for bug in bugs:
    print(bug.title)

db.close()