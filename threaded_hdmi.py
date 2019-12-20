import cv2
import numpy as np
import time
import threading
from queue import Queue

numframes = 2000

class FullScanner(threading.Thread):

    def __init__(self, frameQ, facesQ):
        threading.Thread.__init__(self)
        self.frameQ = frameQ
        self.facesQ = facesQ
        self.started = False
        self.running = True

    def run(self):
        while True:
            while not frameQ.empty():
                t_start = time.time()
                print(f"Scanner started")
                self.facesQ.put(scan(self.frameQ.get()))
                print(f"Scanner done in {time.time() - t_start}")

def scan(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier('/home/xilinx/jupyter_notebooks/base/video/data/'
    'haarcascade_frontalface_default.xml')    
    return face_cascade.detectMultiScale(gray, 1.3, 5)


frameQ = Queue()
facesQ = Queue()

fullScanner = FullScanner(frameQ, facesQ)
fullScanner.daemon = True
frameQ.put(hdmi_in.readframe())  # fill the first frame for the scanner
fullScanner.start()

faces = []
t_started = time.time()
t_start = t_started
for framenum in range(numframes):
    
    frame = hdmi_in.readframe()
    if frameQ.empty() and not facesQ.empty():
        # scanner is done
        frameQ.put(frame)
        faces = facesQ.get()
        print(f"#faces: {len(faces)}")

    size_inc = 50
    for facenum, (x, y, w, h) in enumerate(faces):
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
    hdmi_out.writeframe(frame)
    
    # timings and report
    end_time = time.time()
    dt = end_time - t_start
    t_start = end_time
    if not framenum % 100:
        print(f"avg fps: {framenum/(end_time-t_started):.2f}, cur fps: {1/dt:.2f}, faces {len(faces)}")
    
print("Done!")
fullScanner.running = False