from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from typing import Optional
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Initialize Firebase with environment variables
def initialize_firebase():
    # Get all required Firebase config from environment variables
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
    
    # Validate we have all required fields
    for key, value in firebase_config.items():
        if not value and key != "universe_domain":  # universe_domain has default
            raise ValueError(f"Missing Firebase config: {key}")

    # Initialize Firebase
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)
    return firestore.client()

# Load environment variables
load_dotenv()

try:
    db = initialize_firebase()
except Exception as e:
    print(f"🔥 Failed to initialize Firebase: {str(e)}")
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
        "https://your-render-app.onrender.com"  # Add your Render URL here
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
        return {"message": "Submission received", "id": doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/submissions")
async def get_submissions():
    try:
        docs = db.collection("submissions").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))