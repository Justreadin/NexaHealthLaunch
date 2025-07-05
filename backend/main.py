from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import firebase_admin
from typing import Optional
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase - SIMPLIFIED VERSION
cred = credentials.Certificate("firebase.json")  # or the full path to your file
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Submission(BaseModel):
    name: str
    email: str
    interest: str
    timestamp: Optional[str] = None

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