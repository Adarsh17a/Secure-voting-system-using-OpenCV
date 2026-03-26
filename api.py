from fastapi import FastAPI, UploadFile, File
import numpy as np
import cv2

from core.vote_engine import VoteEngine
from core.register_engine import RegisterEngine

app = FastAPI()

vote_engine = VoteEngine()
register_engine = RegisterEngine()

@app.get("/")
def home():
    return {"message": "Backend running"}

@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    img = await file.read()
    frame = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)

    name = vote_engine.recognize_face(frame)
    return {"name": name}

@app.post("/vote")
def vote(name: str, party: str):
    ok, msg = vote_engine.cast_vote(name, party)
    return {"success": ok, "message": msg}
