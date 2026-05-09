import os
from pymongo import MongoClient
import certifi
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLITE SETUP
SQLALCHEMY_DATABASE_URL = "sqlite:///./libtrack.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# MONGODB SETUP
# This line is the fix: GitHub Actions will provide 'MONGO_URI' automatically
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://singhshivank72_db_user:<db_password>@aimlcluster.qo3ip6c.mongodb.net/?retryWrites=true&w=majority"
)

# Use tlsCAFile only if connecting to Atlas (contains "mongodb+srv")
if "mongodb+srv" in MONGO_URI:
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
else:
    # Local connection for Docker/GitHub Actions (no SSL needed)
    mongo_client = MongoClient(MONGO_URI)

mongo_db = mongo_client["libtrack_database"]
logs_collection = mongo_db["audit_logs"]