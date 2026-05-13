import cv2
import mediapipe as mp
import math
import numpy as np
import requests
import urllib3

from collections import deque

# ===================================
# DISABLE SSL WARNING
# ===================================

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# ===================================
# CLOUD SERVER URL
# ===================================

server_url = "https://healthcare-ai-server.onrender.com/update"

# ===================================
# MEDIAPIPE FACE MESH
# ===================================

mp_face = mp.solutions.face_mesh

face_mesh = mp_face.FaceMesh(

    max_num_faces=1,

    refine_landmarks=True,

    # LOWER CONFIDENCE
    # BETTER INITIAL DETECTION

    min_detection_confidence=0.5,

    min_tracking_confidence=0.5
)

# ===================================
# OPEN CAMERA
# ===================================

# 0 = Laptop Webcam
# 1 = DroidCam
# 2 = External Camera

cap = cv2.VideoCapture(0)

# ===================================
# CHECK CAMERA
# ===================================

if not cap.isOpened():

    print("Unable To Open Camera")

    exit()

# ===================================
# CAMERA RESOLUTION
# ===================================

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)

cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# ===================================
# SMOOTHING BUFFER
# ===================================

angle_buffer = deque(maxlen=6)

# ===================================
# ACTION VARIABLES
# ===================================

last_action = ""

stable_action = "NONE"

action_counter = 0

required_frames = 5

print("Healthcare AI Monitoring Started...")

# ===================================
# MAIN LOOP
# ===================================

while True:

    ret, frame = cap.read()

    if not ret:

        print("Frame Not Received")

        continue

    # ===================================
    # MIRROR VIEW
    # ===================================

    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    # ===================================
    # RGB CONVERSION
    # ===================================

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # ===================================
    # PROCESS FACE
    # ===================================

    result = face_mesh.process(rgb)

    action = "NONE"

    # ===================================
    # FACE DETECTED
    # ===================================

    if result.multi_face_landmarks:

        for landmarks in result.multi_face_landmarks:

            # ===================================
            # EYE LANDMARKS
            # ===================================

            left_eye = landmarks.landmark[33]

            right_eye = landmarks.landmark[263]

            x1 = int(left_eye.x * w)

            y1 = int(left_eye.y * h)

            x2 = int(right_eye.x * w)

            y2 = int(right_eye.y * h)

            # ===================================
            # FACE LANDMARKS
            # ===================================

            nose = landmarks.landmark[1]

            forehead = landmarks.landmark[10]

            chin = landmarks.landmark[152]

            nx = int(nose.x * w)

            ny = int(nose.y * h)

            fx = int(forehead.x * w)

            fy = int(forehead.y * h)

            cx = int(chin.x * w)

            cy = int(chin.y * h)

            # ===================================
            # DRAW LANDMARKS
            # ===================================

            cv2.circle(
                frame,
                (x1, y1),
                4,
                (255, 0, 0),
                -1
            )

            cv2.circle(
                frame,
                (x2, y2),
                4,
                (0, 255, 0),
                -1
            )

            cv2.circle(
                frame,
                (nx, ny),
                4,
                (0, 0, 255),
                -1
            )

            # ===================================
            # DRAW EYE LINE
            # ===================================

            cv2.line(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 255),
                2
            )

            # ===================================
            # HEAD ANGLE
            # ===================================

            angle = math.degrees(

                math.atan2(

                    y2 - y1,

                    x2 - x1
                )
            )

            angle_buffer.append(angle)

            avg_angle = np.mean(angle_buffer)

            # ===================================
            # FACE HEIGHT
            # ===================================

            face_height = abs(cy - fy)

            nose_ratio = (

                ny - fy

            ) / face_height

            # ===================================
            # ADVANCED DETECTION
            # ===================================

            detected_action = "NONE"

            # LEFT TILT

            if avg_angle < -15 and nx < w * 0.45:

                detected_action = "FOOD"

            # RIGHT TILT

            elif avg_angle > 15 and nx > w * 0.55:

                detected_action = "ELECTRICAL"

            # LOOK UP

            elif nose_ratio < 0.38:

                detected_action = "EMERGENCY"

            # LOOK DOWN

            elif nose_ratio > 0.62:

                detected_action = "RESTROOM"

            else:

                detected_action = "NONE"

            # ===================================
            # ACTION STABILIZATION
            # ===================================

            if detected_action == stable_action:

                action_counter += 1

            else:

                stable_action = detected_action

                action_counter = 0

            if action_counter >= required_frames:

                action = stable_action

            else:

                action = "NONE"

            # ===================================
            # SEND TO CLOUD SERVER
            # ===================================

            if action != last_action:

                last_action = action

                print("Detected:", action)

                try:

                    response = requests.post(

                        server_url,

                        json={
                            "value": action
                        },

                        timeout=3,

                        verify=False
                    )

                    print(
                        "SERVER STATUS:",
                        response.status_code
                    )

                except Exception as e:

                    print("SERVER ERROR:", e)

            # ===================================
            # DISPLAY TEXT
            # ===================================

            cv2.putText(

                frame,

                f"ACTION : {action}",

                (20, 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 255, 0),

                2
            )

            cv2.putText(

                frame,

                f"ANGLE : {int(avg_angle)}",

                (20, 80),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (255, 255, 255),

                2
            )

            cv2.putText(

                frame,

                f"RATIO : {round(nose_ratio, 2)}",

                (20, 120),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (255, 255, 255),

                2
            )

    # ===================================
    # NO FACE DETECTED
    # ===================================

    else:

        cv2.putText(

            frame,

            "NO FACE DETECTED",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0, 0, 255),

            2
        )

    # ===================================
    # GUIDE TEXT
    # ===================================

    cv2.putText(

        frame,

        "LEFT = FOOD",

        (20, h - 90),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2
    )

    cv2.putText(

        frame,

        "RIGHT = ELECTRICAL",

        (20, h - 60),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2
    )

    cv2.putText(

        frame,

        "UP = EMERGENCY | DOWN = RESTROOM",

        (20, h - 30),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2
    )

    # ===================================
    # SHOW WINDOW
    # ===================================

    cv2.imshow(
        "Healthcare AI Monitoring",
        frame
    )

    # ===================================
    # ESC TO EXIT
    # ===================================

    if cv2.waitKey(1) & 0xFF == 27:

        break

# ===================================
# CLEANUP
# ===================================

cap.release()

cv2.destroyAllWindows()