"""
Register Engine - Face registration logic extracted from add_faces.py
Captures face data and adds to the recognition database.
"""
import cv2
import pickle
import numpy as np
import os

FRAMES_TOTAL = 51
CAPTURE_AFTER_FRAME = 2


class RegisterEngine:
    """Manages face capture and registration."""

    def __init__(self):
        if not os.path.exists('data/'):
            os.makedirs('data/')
        self.facedetect = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.video = None
        self.faces_data = []
        self.frame_counter = 0

    def start_camera(self, device_id: int = 0) -> bool:
        """Start video capture."""
        self.video = cv2.VideoCapture(device_id)
        self.faces_data = []
        self.frame_counter = 0
        return self.video.isOpened()

    def stop_camera(self) -> None:
        """Release video capture."""
        if self.video:
            self.video.release()
            self.video = None

    def capture_frame(self) -> tuple[bool, object, int]:
        """
        Capture one frame and add face data if detected.
        Returns: (success, frame_bgr, faces_captured_count)
        """
        if not self.video:
            return False, None, 0
        ret, frame = self.video.read()
        if not ret:
            return False, None, len(self.faces_data)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.facedetect.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            crop_img = frame[y:y + h, x:x + w]
            resized_img = cv2.resize(crop_img, (50, 50))
            if len(self.faces_data) <= FRAMES_TOTAL and self.frame_counter % CAPTURE_AFTER_FRAME == 0:
                self.faces_data.append(resized_img)
            self.frame_counter += 1
            cv2.putText(frame, str(len(self.faces_data)), (50, 50),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 255), 1)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 2)
        return True, frame, len(self.faces_data)

    def save_registration(self, name: str) -> tuple[bool, str]:
        """
        Save captured face data to pickle files - identical logic to add_faces.py
        Returns: (success, message)
        """
        min_faces = 25
        if len(self.faces_data) < min_faces:
            return False, f"Need at least {min_faces} faces. Got {len(self.faces_data)}. Keep face in frame longer."

        n = min(len(self.faces_data), FRAMES_TOTAL)
        faces_data = np.array(self.faces_data[:n])
        faces_data = faces_data.reshape((n, -1))

        data_dir = os.path.join(os.getcwd(), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        names_path = os.path.join(data_dir, 'names.pkl')
        faces_path = os.path.join(data_dir, 'faces_data.pkl')

        if 'names.pkl' not in os.listdir(data_dir):
            names = [name] * n
            with open(names_path, 'wb') as f:
                pickle.dump(names, f)
        else:
            with open(names_path, 'rb') as f:
                names = pickle.load(f)
            names = names + [name] * n
            with open(names_path, 'wb') as f:
                pickle.dump(names, f)

        if 'faces_data.pkl' not in os.listdir(data_dir):
            with open(faces_path, 'wb') as f:
                pickle.dump(faces_data, f)
        else:
            with open(faces_path, 'rb') as f:
                faces = pickle.load(f)
            faces = np.append(faces, faces_data, axis=0)
            with open(faces_path, 'wb') as f:
                pickle.dump(faces, f)

        return True, f"Successfully registered {name}"

    def get_progress(self) -> tuple[int, int]:
        """Return (captured, total) for progress display."""
        return len(self.faces_data), FRAMES_TOTAL
