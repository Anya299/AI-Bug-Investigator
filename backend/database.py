import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


# Test database connection
try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        print("Database connected successfully")

except Exception as e:
    print("Connection failed")
    print(e)