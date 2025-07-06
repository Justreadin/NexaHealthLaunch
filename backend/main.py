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

# Initialize Firebase in a more robust way
def init_firebase():
    # Try to get the Firebase config from environment variables
    firebase_config = os.getenv("FIREBASE_CONFIG")
    
    if not firebase_config:
        raise ValueError("FIREBASE_CONFIG environment variable not set")
    
    try:
        # Parse the JSON config
        config_dict = json.loads(firebase_config)
        
        # Initialize Firebase
        cred = credentials.Certificate(config_dict)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except json.JSONDecodeError:
        # If JSON parsing fails, try treating it as a path to a JSON file
        try:
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            raise ValueError(f"Invalid Firebase configuration: {str(e)}")

# Load environment variables
load_dotenv()

try:
    db = init_firebase()
except Exception as e:
    print(f"Failed to initialize Firebase: {str(e)}")
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
        "https://your-render-app-url.onrender.com"  # Add your Render URL
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