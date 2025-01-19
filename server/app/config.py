from dotenv import load_dotenv
import os

load_dotenv()
class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"  # SQLite database path
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")  # Secret key for encrypting session data
