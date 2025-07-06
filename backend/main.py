from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from typing import Optional
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def initialize_firebase():
    try:
        # Get Firebase key from environment variables
        firebase_key_json = os.getenv("FIREBASE_KEY")
        
        if not firebase_key_json:
            raise ValueError("FIREBASE_KEY not found in environment variables")
        
        logger.info("FIREBASE_KEY found in environment variables")
        
        # Clean and parse the JSON
        firebase_key_json = firebase_key_json.strip().replace('\n', '\\n')
        firebase_key = json.loads(firebase_key_json)
        
        # Initialize Firebase
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse FIREBASE_KEY: {e}")
        logger.error(f"Key content: {firebase_key_json[:100]}...")  # Log first 100 chars
        raise
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        raise

try:
    db = initialize_firebase()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")
    raise

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:63342",
        "https://nexa-health-page.vercel.app",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://nexa-health-launch.onrender.com"  # Add your Render URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Submission(BaseModel):
    name: str
    email: str
    interest: str
    timestamp: Optional[str] = None

@app.get("/")
@app.head("/")
async def root():
    return {"message": "NexaHealth_landing page - Your AI Health Companion"}

@app.post("/api/submissions")
async def create_submission(submission: Submission):
    try:
        doc_ref = db.collection("submissions").document()
        doc_ref.set({
            "name": submission.name,
            "email": submission.email,
            "interest": submission.interest,
            "timestamp": submission.timestamp or datetime.now().isoformat(),
            "status": "pending"
        })
        return {"message": "Submission received successfully", "id": doc_ref.id}
    except Exception as e:
        logger.error(f"Submission failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/submissions")
async def get_submissions():
    try:
        docs = db.collection("submissions").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"Failed to get submissions: {e}")
        raise HTTPException(status_code=400, detail=str(e))