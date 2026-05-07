import cv2
import mediapipe as mp
import math
import numpy as np
import requests
from collections import deque

# -----------------------------------
# MOBILE CAMERA URL
# -----------------------------------

url = "http://100.119.195.50:8080/video"

# -----------------------------------
# FLASK SERVER URL
# -----------------------------------

server_url = "http://127.0.0.1:5000/update"

# -----------------------------------
# MEDIAPIPE SETUP
# -----------------------------------

mp_face = mp.solutions.face_mesh

face_mesh = mp_face.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.85,
    min_tracking_confidence=0.85
)

# -----------------------------------
# CAMERA
# -----------------------------------

cap = cv2.VideoCapture(url)

# -----------------------------------
# SMOOTHING
# -----------------------------------

angle_buffer = deque(maxlen=7)

last_action = ""

print("Healthcare AI Started...")

while True:

    ret, frame = cap.read()

    if not ret:
        print("Camera Not Connected")
        break

    # Mirror View
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb)

    action = "NONE"

    # -----------------------------------
    # FACE DETECTION
    # -----------------------------------

    if result.multi_face_landmarks:

        for landmarks in result.multi_face_landmarks:

            # LEFT EYE
            left_eye = landmarks.landmark[33]

            # RIGHT EYE
            right_eye = landmarks.landmark[263]

            x1 = int(left_eye.x * w)
            y1 = int(left_eye.y * h)

            x2 = int(right_eye.x * w)
            y2 = int(right_eye.y * h)

            # DRAW EYES
            cv2.circle(frame, (x1, y1), 5, (255, 0, 0), -1)
            cv2.circle(frame, (x2, y2), 5, (0, 255, 0), -1)

            # DRAW LINE
            cv2.line(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 255),
                2
            )

            # -----------------------------------
            # HEAD TILT ANGLE
            # -----------------------------------

            angle = math.degrees(
                math.atan2(y2 - y1, x2 - x1)
            )

            angle_buffer.append(angle)

            avg_angle = np.mean(angle_buffer)

            # -----------------------------------
            # ACTION DETECTION
            # -----------------------------------

            # LEFT TILT
            if avg_angle < -12:
                action = "FOOD"

            # RIGHT TILT
            elif avg_angle > 12:
                action = "ELECTRICAL"

            # LOOK UP
            elif y1 < h * 0.30 and y2 < h * 0.30:
                action = "EMERGENCY"

            # LOOK DOWN
            elif y1 > h * 0.45 and y2 > h * 0.45:
                action = "RESTROOM"

            else:
                action = "NONE"

            # -----------------------------------
            # SEND TO SERVER
            # -----------------------------------

            if action != last_action:

                last_action = action

                print("Detected:", action)

                try:

                    response = requests.post(
                        server_url,
                        json={
                            "value": action
                        }
                    )

                    print("Sent To Server")

                except:
                    print("Server Connection Failed")

            # -----------------------------------
            # DISPLAY TEXT
            # -----------------------------------

            cv2.putText(
                frame,
                f"ACTION : {action}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                3
            )

            cv2.putText(
                frame,
                f"ANGLE : {int(avg_angle)}",
                (30, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

    else:

        cv2.putText(
            frame,
            "NO FACE DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

    # -----------------------------------
    # GUIDE TEXT
    # -----------------------------------

    cv2.putText(
        frame,
        "LEFT TILT = FOOD",
        (20, h - 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "RIGHT TILT = ELECTRICAL",
        (20, h - 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "UP = EMERGENCY | DOWN = RESTROOM",
        (20, h - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # -----------------------------------
    # SHOW WINDOW
    # -----------------------------------

    cv2.imshow("Healthcare AI Monitoring", frame)

    # ESC TO EXIT
    if cv2.waitKey(1) & 0xFF == 27:
        break

# -----------------------------------
# CLEANUP
# -----------------------------------

cap.release()
cv2.destroyAllWindows()