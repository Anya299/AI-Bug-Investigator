from database import SessionLocal
from models import BugPattern


db = SessionLocal()


patterns = [
    {
        "error_type": "ModuleNotFoundError",
        "error_message": "No module named package",
        "language": "Python",
        "framework": "General",
        "root_cause": "Required dependency is missing or import path is incorrect.",
        "common_fix": "Install missing package using pip and verify import statements.",
        "tags": "python,dependency,import",
        "success_rate": 95.0,
        "is_verified": True
    },

    {
        "error_type": "Database Connection Error",
        "error_message": "Could not connect to database",
        "language": "Python",
        "framework": "SQLAlchemy",
        "root_cause": "Wrong database URL, credentials, host, or port configuration.",
        "common_fix": "Check DATABASE_URL and verify database credentials.",
        "tags": "database,postgres,sqlalchemy",
        "success_rate": 90.0,
        "is_verified": True
    },

    {
        "error_type": "CORS Error",
        "error_message": "Blocked by CORS policy",
        "language": "Python",
        "framework": "FastAPI",
        "root_cause": "Frontend origin is not allowed by backend.",
        "common_fix": "Configure CORSMiddleware with allowed origins.",
        "tags": "fastapi,frontend,cors",
        "success_rate": 92.0,
        "is_verified": True
    },

    {
        "error_type": "JWT Authentication Error",
        "error_message": "Invalid token",
        "language": "Python",
        "framework": "FastAPI",
        "root_cause": "Expired token or incorrect JWT secret configuration.",
        "common_fix": "Generate a new token and verify JWT settings.",
        "tags": "jwt,authentication,security",
        "success_rate": 88.0,
        "is_verified": True
    }
]


for item in patterns:
    bug = BugPattern(**item)
    db.add(bug)


db.commit()

print("Bug patterns added successfully!")

db.close()