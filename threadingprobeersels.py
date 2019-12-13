import cv2
import numpy as np
import PIL.Image
import time
import threading
import copy

numframes = 1000
_all = True

face_cascade = cv2.CascadeClassifier(
    '/home/xilinx/jupyter_notebooks/base/video/data/'
    'haarcascade_frontalface_default.xml')

class FullScanner(threading.Thread):

    def __init__(self, frame):
        threading.Thread.__init__(self)
        self.frame = frame
        self.faces = []
        self.started = False
        self.running = True

    def run(self):
        t_start = time.time()
        print(f"Scanner started")
        self.faces = scan(self.frame)
        self.started = False
        print(f"Scanner done in {time.time()-t_start}; #faces: {len(self.faces)}")
        time.sleep(0.1)

def scan(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return face_cascade.detectMultiScale(gray, 1.3, 5)


fullScanner = FullScanner()
fullScanner.daemon = True
fullScanner.start()
for framenum in range(numframes):
    t_start = time.time()
    frame = hdmi_in.readframe()
    if not fullScanner.started:
        print("1")
        faces = fullScanner.faces
        print("2")
        fullScanner.frame = copy.deepcopy(frame)
        print("3")
        fullScanner.started = True
        print("4")
    frame = hdmi_in.readframe()
    size_inc = 50
    for facenum, (x, y, w, h) in enumerate(faces):
        
        small_frame = frame[y-size_inc:y+h+size_inc, x-size_inc:x+w+size_inc]
        small_faces = scan(small_frame)
#         img = PIL.Image.fromarray(small_frame)
        cv2.rectangle(frame,(x-size_inc,y-size_inc),(x+w+size_inc,y+h+size_inc),(255,255,0),2)
        
        if len(small_faces) > 1: print("Warning, multiple small faces")
        elif len(small_faces) == 0:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,255),2)
        for (xs, ys, ws, hs) in small_faces:
            faces[facenum] = (x+xs-size_inc,y+ys-size_inc, ws, hs)
            cv2.rectangle(frame,(x+xs-size_inc,y+ys-size_inc),(x+xs+ws-size_inc,y+ys+hs-size_inc),(255,0,0),2)
            break
             
#     print(f"dt: {time.time()-t_start}; #faces: {len(faces)}")
    hdmi_out.writeframe(frame)
fullScanner.running = False