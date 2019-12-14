import cv2
import mss
import numpy as np
import time
import threading
from queue import Queue


numframes = 1000
_all = True

def MSS2CV2(im):
    im = np.flip(np.array(im)[:, :, :3], 2)  # 1
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)  # 2
    return im


def localframe(region):
    with mss.mss() as sct:
        while True:
            yield MSS2CV2(sct.grab(region))

framegen = localframe({
    "left": 0,
    "top": 0,
    "width": 800,
    "height": 600
})

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
            time.sleep(0.1)

def scan(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    return face_cascade.detectMultiScale(gray, 1.3, 5)


frameQ = Queue()
facesQ = Queue()

fullScanner = FullScanner(frameQ, facesQ)
fullScanner.daemon = True
frameQ.put(next(framegen))  # fill the first frame for the scanner
fullScanner.start()

faces = []

for framenum in range(numframes):
    t_start = time.time()
    # frame = hdmi_in.readframe()
    frame = next(framegen)
    if frameQ.empty() and not facesQ.empty():
        # scanner is done
        frameQ.put(frame)
        faces = facesQ.get()
        print(f"#faces: {len(faces)}")

    size_inc = 50
    for facenum, (x, y, w, h) in enumerate(faces):

        small_frame = frame[max(0, y - size_inc):y + h + size_inc, max(0, x - size_inc):x + w + size_inc]
        small_faces = scan(small_frame)
        cv2.rectangle(frame, (x - size_inc, y - size_inc), (x + w + size_inc, y + h + size_inc), (255, 255, 0), 2)

        if len(small_faces) > 1:
            print("Warning, multiple small faces")
        elif len(small_faces) == 0:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
        for (xs, ys, ws, hs) in small_faces:
            faces[facenum] = (x + xs - size_inc, y + ys - size_inc, ws, hs)
            cv2.rectangle(frame, (x + xs - size_inc, y + ys - size_inc),
                          (x + xs + ws - size_inc, y + ys + hs - size_inc), (255, 0, 0), 2)
            break
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
#     print(f"dt: {time.time()-t_start}; #faces: {len(faces)}")
#     hdmi_out.writeframe(frame)

fullScanner.running = False
framegen.close()