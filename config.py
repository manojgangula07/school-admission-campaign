# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if you're using one)
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'you-will-never-guess'
    # Use absolute path for database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'school.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False