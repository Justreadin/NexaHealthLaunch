from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv
from datetime import datetime
import logging

# ─────────────────────────────
# Logging & env-vars
# ─────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # .env files still work for local dev

# ─────────────────────────────
# Firebase helper
# ─────────────────────────────
class FirebaseManager:
    """
    Singleton wrapper around Firebase Admin SDK.
    Looks for a JSON key file at:
      1. FIREBASE_KEY_PATH          (highest priority)
      2. GOOGLE_APPLICATION_CREDENTIALS
      3. /etc/secrets/firebase_key.json   (Render’s default mount point)
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_firebase()
        return cls._instance

    def _initialize_firebase(self):
        cred_path = (
            os.getenv("FIREBASE_KEY_PATH")
            or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            or "/etc/secrets/firebase_key.json"
        )

        if not os.path.exists(cred_path):
            raise RuntimeError(
                f"Firebase key file not found at {cred_path}. "
                "Set GOOGLE_APPLICATION_CREDENTIALS or FIREBASE_KEY_PATH."
            )

        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("✔️  Firebase Admin SDK initialized (%s)", cred_path)

        self._verify_firebase_connection()

    @staticmethod
    def _verify_firebase_connection():
        """Fail fast if the service account is wrong or revoked."""
        try:
            next(auth.list_users(max_results=1), None)
            logger.debug("Firebase connection verified")
        except Exception as exc:
            logger.error("❌ Firebase connection failed: %s", exc)
            raise

    def get_firestore_client(self):
        self._verify_firebase_connection()
        return firestore.client()


# ─────────────────────────────
# Initialise Firebase once
# ─────────────────────────────
try:
    firebase_manager = FirebaseManager()
    db = firebase_manager.get_firestore_client()
except Exception as exc:
    logger.critical("🔥 Could not start because Firebase failed: %s", exc)
    raise  # Crash fast so Render shows the real error

# ─────────────────────────────
# FastAPI setup
# ─────────────────────────────
app = FastAPI()

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
        "https://your-actual-frontend-domain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────
# Pydantic models
# ─────────────────────────────
class Submission(BaseModel):
    name: str
    email: str
    interest: str
    timestamp: Optional[str] = None


# ─────────────────────────────
# Routes
# ─────────────────────────────
@app.get("/")
async def root():
    return {"message": "NexaHealth Landing Page API"}


@app.post("/api/submissions")
async def create_submission(submission: Submission, request: Request):
    try:
        logger.info("Incoming submission: %s", submission.dict())

        # Very quick e-mail sanity check
        if "@" not in submission.email or "." not in submission.email:
            raise HTTPException(status_code=400, detail="Invalid email format")

        doc_ref = db.collection("submissions").document()
        doc_data = {
            "name": submission.name,
            "email": submission.email,
            "interest": submission.interest,
            "timestamp": submission.timestamp or datetime.utcnow().isoformat(),
            "status": "pending",
        }

        doc_ref.set(doc_data)
        logger.info("Document created with ID: %s", doc_ref.id)

        return {"message": "Submission received", "id": doc_ref.id, "data": doc_data}

    except Exception as exc:
        logger.error("Submission error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/submissions")
async def get_submissions():
    try:
        docs = db.collection("submissions").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as exc:
        logger.error("Error fetching submissions: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
