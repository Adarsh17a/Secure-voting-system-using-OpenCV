"""
Vote Engine - Core voting logic extracted from give_vote.py
Uses face recognition to identify voters and record votes to vote.csv
"""
from sklearn.neighbors import KNeighborsClassifier
import cv2
import numpy as np
import pickle
import os
import csv
import time
from datetime import datetime

VOTE_CSV = "vote.csv"
COL_NAMES = ['Name', 'VOTE', 'DATE', 'TIME']
PARTIES = ['BJP', 'CONGRESS', 'AAP', 'NOTA']


def _speak(text: str) -> None:
    """Text-to-speech (Windows only). Silent on other platforms."""
    try:
        from win32com.client import Dispatch
        speaker = Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
    except Exception:
        pass


def _check_if_voted(name: str) -> bool:
    """Check if voter has already cast a vote."""
    name_str = str(name).strip()
    try:
        with open(VOTE_CSV, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row and str(row[0]).strip() == name_str:
                    return True
    except FileNotFoundError:
        pass
    return False


def _record_vote(name: str, party: str) -> None:
    """Record vote to vote.csv with Name, VOTE, DATE, TIME."""
    ts = time.time()
    date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    timestamp = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    exist = os.path.isfile(VOTE_CSV)

    with open(VOTE_CSV, "a", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not exist:
            writer.writerow(COL_NAMES)
        writer.writerow([str(name).strip(), party, date, timestamp])


class VoteEngine:
    """Manages face recognition model and voting operations."""

    def __init__(self):
        if not os.path.exists('data/'):
            os.makedirs('data/')
        self.facedetect = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.video = None
        self.knn = None
        self._load_model()

    def _load_model(self) -> bool:
        """Load KNN model from pickle files."""
        try:
            data_dir = os.path.join(os.getcwd(), 'data')
            names_path = os.path.join(data_dir, 'names.pkl')
            faces_path = os.path.join(data_dir, 'faces_data.pkl')
            with open(names_path, 'rb') as f:
                labels = pickle.load(f)
            with open(faces_path, 'rb') as f:
                faces = pickle.load(f)
            self.knn = KNeighborsClassifier(n_neighbors=5)
            self.knn.fit(faces, labels)
            return True
        except FileNotFoundError:
            return False

    def reload_model(self) -> bool:
        """Reload model from disk (call after new user registration)."""
        return self._load_model()

    def start_camera(self, device_id: int = 0) -> bool:
        """Start video capture."""
        self.video = cv2.VideoCapture(device_id)
        return self.video.isOpened()

    def stop_camera(self) -> None:
        """Release video capture."""
        if self.video:
            self.video.release()
            self.video = None

    def get_frame_with_detection(self) -> tuple[bool, np.ndarray | None, str | None]:
        """
        Get a frame with face detection overlay.
        Returns: (success, frame_bgr, detected_name or None)
        """
        if not self.video or not self.knn:
            return False, None, None
        ret, frame = self.video.read()
        if not ret:
            return False, None, None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.facedetect.detectMultiScale(gray, 1.3, 5)
        output_name = None
        for (x, y, w, h) in faces:
            crop_img = frame[y:y + h, x:x + w]
            resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
            pred = self.knn.predict(resized_img)[0]
            output_name = str(pred).strip()  # Ensure plain string for CSV/storage
            cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 2)
            cv2.rectangle(frame, (x, y - 40), (x + w, y), (50, 50, 255), -1)
            cv2.putText(frame, output_name, (x, y - 10),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
        return True, frame, output_name

    def check_already_voted(self, name: str) -> bool:
        """Check if this voter has already voted."""
        return _check_if_voted(name)

    def cast_vote(self, name: str, party: str) -> tuple[bool, str]:
        """
        Record vote and speak confirmation.
        Returns: (success, message)
        """
        if party not in PARTIES:
            return False, "Invalid party"
        _speak("YOUR VOTE HAS BEEN RECORDED")
        _record_vote(name, party)
        _speak("THANK YOU FOR PARTICIPATING IN THE VOTING PROCESS.")
        return True, "Vote recorded successfully"

    def speak_already_voted(self) -> None:
        """Announce that voter has already voted."""
        _speak("YOU HAVE ALREADY VOTED.")
