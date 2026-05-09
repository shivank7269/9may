from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
import os

load_dotenv()


# --- SQLITE SETUP (For Relational Data) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./libtrack.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- MONGODB ATLAS SETUP (For Logs) ---
db_password = os.getenv('DB_PASS')
db_user = os.getenv('DB_USER')
MONGO_URI = f"mongodb+srv://{db_user}:{db_password}@aimlcluster.qo3ip6c.mongodb.net/?retryWrites=true&w=majority"

# certifi is used to prevent SSL errors when connecting to Atlas
mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
mongo_db = mongo_client["libtrack_database"]
logs_collection = mongo_db["audit_logs"]