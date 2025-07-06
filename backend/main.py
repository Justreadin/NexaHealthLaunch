from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from typing import Optional
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase with environment variables
def initialize_firebase():
    try:
        firebase_config = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com")
        }
        
        # Validate config
        for key, value in firebase_config.items():
            if not value and key != "universe_domain":
                raise ValueError(f"Missing Firebase config: {key}")

        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        logger.error(f"Firebase initialization failed: {str(e)}")
        raise

# Load environment variables
load_dotenv()

try:
    db = initialize_firebase()
except Exception as e:
    logger.error(f"🔥 Critical: Failed to initialize Firebase: {str(e)}")
    raise

app = FastAPI()

# CORS Configuration - Update with your actual frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:63342",
        "https://nexa-health-page.vercel.app",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://lyrecal.onrender.com",  # Your Render URL
        "https://your-actual-frontend-domain.com"  # Add your production frontend URL
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
async def root():
    return {"message": "NexaHealth Landing Page API"}

@app.post("/api/submissions")
async def create_submission(submission: Submission, request: Request):
    try:
        logger.info(f"Incoming submission: {submission.dict()}")
        logger.info(f"Headers: {request.headers}")
        
        # Validate email format
        if "@" not in submission.email or "." not in submission.email:
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        doc_ref = db.collection("submissions").document()
        doc_data = {
            "name": submission.name,
            "email": submission.email,
            "interest": submission.interest,
            "timestamp": submission.timestamp or datetime.now().isoformat(),
            "status": "pending"
        }
        
        doc_ref.set(doc_data)
        logger.info(f"Document created with ID: {doc_ref.id}")
        
        return {
            "message": "Submission received",
            "id": doc_ref.id,
            "data": doc_data
        }
    except Exception as e:
        logger.error(f"Submission error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e) if "detail" not in str(e) else str(e))