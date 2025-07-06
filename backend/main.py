from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
import base64
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.auth.transport import requests
from google.oauth2 import service_account
from dotenv import load_dotenv
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class FirebaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
            cls._instance._initialize_firebase()
        return cls._instance
    
    def _initialize_firebase(self, retry_count=0):
        """Initialize Firebase Admin SDK with error handling and retry logic"""
        max_retries = 3
        try:
            # Get the base64 encoded key from environment
            firebase_key_b64 = os.getenv("FIREBASE_KEY")
            
            if not firebase_key_b64:
                raise ValueError("FIREBASE_KEY is not set in environment variables")

            # Decode from base64 to JSON string
            firebase_key_json_str = base64.b64decode(firebase_key_b64).decode('utf-8')
            
            # Parse JSON string into dictionary
            firebase_config = json.loads(firebase_key_json_str)

            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
                
            # Verify the credentials work
            self._verify_firebase_connection()
            
        except Exception as e:
            logger.error(f"Firebase initialization error (attempt {retry_count + 1}): {str(e)}")
            if retry_count < max_retries - 1:
                logger.info(f"Retrying Firebase initialization... ({retry_count + 1}/{max_retries})")
                self._initialize_firebase(retry_count + 1)
            else:
                logger.error("Max retries reached for Firebase initialization")
                raise
    
    def _verify_firebase_connection(self):
        """Verify that Firebase connection is working"""
        try:
            # Try to list users as a test
            auth.list_users(max_results=1)
            logger.debug("Firebase connection verified successfully")
        except Exception as e:
            logger.error(f"Firebase connection verification failed: {str(e)}")
            raise
    
    def refresh_firebase_token(self):
        """Refresh the Firebase authentication token"""
        try:
            firebase_key_b64 = os.getenv("FIREBASE_KEY")
            firebase_key_json_str = base64.b64decode(firebase_key_b64).decode('utf-8')
            firebase_config = json.loads(firebase_key_json_str)
            
            creds = service_account.Credentials.from_service_account_info(
                firebase_config,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            request = requests.Request()
            creds.refresh(request)
            logger.info("Firebase token refreshed successfully")
            return creds.token
        except Exception as e:
            logger.error(f"Failed to refresh Firebase token: {str(e)}")
            raise
    
    def get_firestore_client(self):
        """Get Firestore client with connection verification"""
        try:
            self._verify_firebase_connection()
            return firestore.client()
        except Exception as e:
            logger.error(f"Firestore connection error: {str(e)}")
            try:
                self.refresh_firebase_token()
                return firestore.client()
            except Exception as refresh_error:
                logger.error(f"Failed to recover Firestore connection: {str(refresh_error)}")
                raise

# Initialize Firebase
try:
    firebase_manager = FirebaseManager()
    db = firebase_manager.get_firestore_client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"🔥 Critical: Failed to initialize Firebase: {str(e)}")
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
        "https://lyrecal.onrender.com",
        "https://your-actual-frontend-domain.com"
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

@app.get("/api/submissions")
async def get_submissions():
    try:
        docs = db.collection("submissions").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"Error fetching submissions: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))