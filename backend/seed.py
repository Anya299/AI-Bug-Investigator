from database import SessionLocal
from models import BugReport


db = SessionLocal()


bug = BugReport(
    title="FastAPI validation error",
    language="Python",
    framework="FastAPI",
    description="API returns 422 error when JSON input is wrong",
    stack_trace="ValidationError: field required",
    severity="medium",
    status="open"
)


db.add(bug)
db.commit()

print("Bug case added successfully ✅")

db.close()