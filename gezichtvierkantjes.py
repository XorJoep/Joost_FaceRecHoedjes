
# coding: utf-8

# ### Face detection with blurring on FPGA

# ### Step 1: Import stuff

# In[18]:


import cv2
import numpy as np
import time
import threading
from queue import Queue

from pynq import Overlay
from pynq import MMIO
from pynq.overlays.base import BaseOverlay
from pynq.lib.video import *

from pynq.lib import AxiGPIO


# ### Step 2: Define FPGA class

# In[32]:


class FPGA_Connection():
    def __init__(self):
        self.square_address = MMIO(0x43C80000,0x10000)
        self.port_x = 0x10
        self.port_y = 0x18
        self.port_w = 0x20
        self.port_h = 0x28
        self.port_OnOffToggle = 0x30
        self.disabled = False
        self.turnOn()

    def writeSquare(self, x, y, w, h):
        #port x
        self.write(self.port_x, x)
        #port y
        self.write(self.port_y, y)
        #port w
        self.write(self.port_w, w)
        #port h
        self.write(self.port_h, h)
        
    def isDisabled(self):
        dtprint()

    def turnOn(self):
        self.disabled = False
        self.write(self.port_OnOffToggle, self.disabled)
        
    def turnOff(self):
        self.disabled = True
        self.write(self.port_OnOffToggle, self.disabled)

    def toggle(self):
        self.disabled = not self.disabled
        self.write(self.port_OnOffToggle, self.disabled)

    def write(self, port_address, value):
        self.square_address.write(port_address, int(value))


# ### Step 3: Define scan class

# In[20]:


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


# ### Step 4: Define functions

# In[21]:


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


# ### Step 5: Download overlay

# In[22]:


ol = Overlay("/home/xilinx/jupyter_notebooks/blurringdreams.bit")
ol.download()
dtprint("Overlay downloaded")


# ### Step 6: setup HDMI

# In[23]:


hdmi_in = ol.video.hdmi_in
hdmi_out = ol.video.hdmi_out
dtprint("HDMI video in & out set")

hdmi_in.configure(PIXEL_RGBA)
hdmi_out.configure(hdmi_in.mode, PIXEL_RGBA)
dtprint("HDMI video in & out configured")

hdmi_in.start()
hdmi_out.start()
dtprint("HDMI video streams started")


# ### Step 6.5: Tie HDMI

# In[24]:


hdmi_in.tie(hdmi_out)


# ### Step 7: Create FPGA object

# In[33]:


FPGA = FPGA_Connection()
dtprint("Created fgpa object")


# ### Step 8: Setup switch reading

# In[28]:


switches_ip = ol.ip_dict['switches_gpio']
switches = AxiGPIO(switches_ip).channel1
# switches.read()


# ### MAIN THREAD

# In[34]:


frameQ = Queue()
facesQ = Queue()

fullScanner = FullScanner(frameQ, facesQ)
fullScanner.daemon = True
frameQ.put(hdmi_in.readframe())  # fill the first frame for the scanner
fullScanner.start()

t_started = time.time()

prevRead = switches.read()

workTime = 30 # seconds

while time.time() - t_started < workTime:
    
    if frameQ.empty() and not facesQ.empty():
        frame = hdmi_in.readframe()
        frameQ.put(frame)
        faces = facesQ.get()
        dtprint(f"#faces: {len(faces)}")
        if len(faces) > 0:
            FPGA.writeSquare(*faces[0])
        else:
            FPGA.turnOff()
            
    if switches.read() != prevRead:
        prevRead = switches.read()
        FPGA.toggle()
    
dtprint("Done!")
fullScanner.running = False


# ### Shutdown everything

# In[17]:


hdmi_out.close()
hdmi_in.close()

dtprint("HDMI Closed")

