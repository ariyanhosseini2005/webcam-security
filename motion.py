import cv2
import os
import json
import time
from datetime import datetime
from threading import Thread, Lock
import numpy as np
import notifier

with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

PHOTOS_DIR = 'photos'
VIDEOS_DIR = 'videos'
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

class MotionDetector(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.cam_index = CONFIG.get('CAMERA_INDEX', 0)
        self.w = CONFIG.get('FRAME_WIDTH', 640)
        self.h = CONFIG.get('FRAME_HEIGHT', 480)
        self.min_area = CONFIG.get('MIN_AREA', 1200)
        self.sens = CONFIG.get('MOTION_SENSITIVITY', 0.45)
        self.hold_secs = CONFIG.get('RECORD_AFTER_MOTION_SECONDS', 7)

        self.cap = cv2.VideoCapture(self.cam_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h)

        self.bg_sub = cv2.createBackgroundSubtractorMOG2(history=400, varThreshold=int(50 + (1-self.sens)*100), detectShadows=True)

        self.lock = Lock()
        self.latest_frame = None
        self.motion_active = False

        self.writer = None
        self.last_motion_time = 0
        self.running = True

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            frame = cv2.resize(frame, (self.w, self.h))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fgmask = self.bg_sub.apply(gray)
            fgmask = cv2.threshold(fgmask, 244, 255, cv2.THRESH_BINARY)[1]
            fgmask = cv2.dilate(fgmask, None, iterations=2)

            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_detected = False
            for c in contours:
                if cv2.contourArea(c) < self.min_area:
                    continue
                motion_detected = True
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            now = time.time()

            if motion_detected:
                if not self.motion_active:
                    self.motion_active = True
                    self.start_recording()
                    photo_path = self.save_photo(frame)
                    notifier.send_message("⚠️ Motion detected! Recording started.")
                    if photo_path:
                        notifier.send_photo(photo_path, caption="Snapshot")
                self.last_motion_time = now

            if self.motion_active and (now - self.last_motion_time) > self.hold_secs:
                self.stop_recording()
                self.motion_active = False
                notifier.send_message("✅ Motion ended. Recording stopped.")

            if self.writer is not None:
                self.writer.write(frame)

            with self.lock:
                self.latest_frame = frame.copy()

        self.cleanup()

    def start_recording(self):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_path = os.path.join(VIDEOS_DIR, f"motion_{ts}.mp4")
        self.writer = cv2.VideoWriter(video_path, fourcc, 20.0, (self.w, self.h))

    def stop_recording(self):
        if self.writer is not None:
            self.writer.release()
            self.writer = None

    def save_photo(self, frame):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        photo_path = os.path.join(PHOTOS_DIR, f"snap_{ts}.jpg")
        try:
            cv2.imwrite(photo_path, frame)
            return photo_path
        except Exception:
            return None

    def get_jpeg(self):
        with self.lock:
            frame = self.latest_frame.copy() if self.latest_frame is not None else None
        if frame is None:
            blank = np.zeros((self.h, self.w, 3), dtype=np.uint8)
            ret, buf = cv2.imencode('.jpg', blank)
            return buf.tobytes()
        ret, buf = cv2.imencode('.jpg', frame)
        return buf.tobytes()

    def stop(self):
        self.running = False

    def cleanup(self):
        if self.writer is not None:
            self.writer.release()
        if self.cap is not None:
            self.cap.release()
