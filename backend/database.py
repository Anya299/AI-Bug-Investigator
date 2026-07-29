import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

from config import get_settings

settings = get_settings()

DATABASE_URL = settings.database_url


engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def check_database():

    try:
        db = SessionLocal()

        db.execute(text("SELECT 1"))

        db.close()

        return True

    except Exception:
        return False


# Test database connection
try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        print("Database connected successfully")

except Exception as e:
    print("Connection failed")
    print(e)