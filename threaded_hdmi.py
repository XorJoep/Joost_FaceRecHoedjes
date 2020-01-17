import cv2
import numpy as np
import time
import threading
from queue import Queue

from pynq import Overlay
from pynq import MMIO
from pynq.overlays.base import BaseOverlay
from pynq.lib.video import *


class FPGA_Connection():
    def __init__(self):
        self.square_address = MMIO(0x43C80000,0x10000)
        self.port_x = 0x10
        self.port_y = 0x18
        self.port_w = 0x20
        self.port_h = 0x28
        self.port_OnOffToggle = 0x30
        self.On = True
        self.turnOn()

    def writeSquare(x, y, w, h)
        #port x
        self.write(self.port_x, x)
        #port y
        self.write(self.port_y, y)
        #port w
        self.write(self.port_w, w)
        #port h
        self.write(self.port_h, h) 

    def turnOn():
        self.on = True
        self.write(self.port_OnOffToggle, int(self.on))

    def turnOff():
        self.on = False
        self.write(self.port_OnOffToggle, int(self.on))

    def toggle():
        self.on = not self.on
        self.write(self.port_OnOffToggle, int(self.on))

    def write(port_address, value):
        self.square_address.write(port_address, value)


class FullScanner(threading.Thread):

    def __init__(self, frameQ, facesQ):
        threading.Thread.__init__(self)
        self.frameQ = frameQ
        self.facesQ = facesQ
        self.started = False
        self.running = True

    def run(self):
        while True:
            while not frameQ.empty() and self.running:
                self.facesQ.put(scan(self.frameQ.get()))

def scan(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier('/home/xilinx/jupyter_notebooks/base/video/data/'
    'haarcascade_frontalface_default.xml')    
    return face_cascade.detectMultiScale(gray, 1.3, 5)

# print message with timed elapsed since starttime
def dtprint(msg):
    print(f"[{time.time()-dtprint.t_started:.4f}] {msg}")


dtprint.t_started = time.time()
dtprint("Started")

ol = Overlay("/home/xilinx/jupyter_notebooks/dreams2.bit")
ol.download()
dtprint("Overlay downloaded")

hdmi_in = ol.video.hdmi_in
hdmi_out = ol.video.hdmi_out
dtprint("HDMI video in & out set")

hdmi_in.configure(PIXEL_RGBA)
hdmi_out.configure(hdmi_in.mode, PIXEL_RGBA)
dtprint("HDMI video in & out configured")

hdmi_in.start()
hdmi_out.start()
dtprint("HDMI video streams started")

# hdmi_in.tie(hdmi_out)
# dtprint("HDMI video tied")

FPGA = FPGA_Connection()

frameQ = Queue()
facesQ = Queue()

fullScanner = FullScanner(frameQ, facesQ)
fullScanner.daemon = True
frameQ.put(hdmi_in.readframe())  # fill the first frame for the scanner
fullScanner.start()

t_started = time.time()
t_start = t_started

numframes = 2000

for framenum in range(numframes):
    
    frame = hdmi_in.readframe()
    if frameQ.empty() and not facesQ.empty():
        frameQ.put(frame)
        faces = facesQ.get()
        print(f"#faces: {len(faces)}")
        if len(faces) > 0:
            FPGA.writeSquare(*faces[0])
    
    hdmi_out.writeframe(frame)
    
    # timings and report
    # end_time = time.time()
    # dt = end_time - t_start
    # t_start = end_time
    # if not framenum % 100:
    #     print(f"avg fps: {framenum/(end_time-t_started):.2f}, cur fps: {1/dt:.2f}, faces {len(faces)}")
    

fullScanner.running = False

hdmi_out.close()
hdmi_in.close()

dtprint("HDMI Closed")