# test_db_connection.py
from sqlalchemy import create_engine

DATABASE_URL = 'postgresql://postgres:2001@localhost:5432/school'
engine = create_engine(DATABASE_URL)
try:
    engine.connect()
    print("Database connection successful!")
except Exception as e:
    print(f"Error connecting to database: {e}")
