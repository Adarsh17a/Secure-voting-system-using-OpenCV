def recognize_face(self, frame):
    if self.knn is None:
        return None

    try:
        import cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return None

        for (x, y, w, h) in faces:
            face = frame[y:y+h, x:x+w]
            face = cv2.resize(face, (50, 50)).flatten().reshape(1, -1)

            name = self.knn.predict(face)[0]
            return name

        return None

    except Exception as e:
        print("Error:", e)
        return None
      
