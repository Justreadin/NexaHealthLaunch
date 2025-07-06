from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import firebase_admin
from typing import Optional
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Firebase key from environment variables
firebase_key_json = os.getenv("Firebase_key")

# Initialize Firebase using the key from .env
if not firebase_key_json:
    raise ValueError("Firebase_key not found in environment variables")

# Parse the JSON string from the environment variable
firebase_key = json.loads(firebase_key_json)

# Initialize Firebase with the credentials
cred = credentials.Certificate(firebase_key)
firebase_admin.initialize_app(cred)
db = firestore.client()

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
        "http://127.0.0.1:5500"
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
        # Add to Firestore
        doc_ref = db.collection("submissions").document()
        doc_ref.set({
            "name": submission.name,
            "email": submission.email,
            "interest": submission.interest,
            "timestamp": submission.timestamp,
            "status": "pending"
        })
        
        return {"message": "Submission received successfully", "id": doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/submissions")
async def get_submissions():
    try:
        docs = db.collection("submissions").stream()
        submissions = []
        for doc in docs:
            submissions.append(doc.to_dict())
        return submissions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))