from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2

from core.vote_engine import VoteEngine
from core.register_engine import RegisterEngine

# ---------------- APP INIT ----------------
app = FastAPI()

# ---------------- CORS (FIXED) ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (you can restrict later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- INIT ENGINES ----------------
vote_engine = VoteEngine()
register_engine = RegisterEngine()

# ---------------- ROUTES ----------------

@app.get("/")
def home():
    return {"message": "Backend running successfully"}

# 🔥 FACE RECOGNITION
@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    try:
        # read image
        img = await file.read()
        nparr = np.frombuffer(img, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"error": "Invalid image"}

        # call your logic
        name = vote_engine.recognize_face(frame)

        if not name:
            return {"name": "Unknown"}

        return {"name": name}

    except Exception as e:
        return {"error": str(e)}

# 🔥 VOTE
@app.post("/vote")
def vote(name: str, party: str):
    try:
        ok, msg = vote_engine.cast_vote(name, party)

        return {
            "success": ok,
            "message": msg
        }

    except Exception as e:
        return {"error": str(e)}
