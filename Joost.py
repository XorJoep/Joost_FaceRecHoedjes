
# coding: utf-8

# In[1]:


from pynq import Overlay
from pynq import MMIO
from pynq.overlays.base import BaseOverlay
from pynq.lib.video import *

ol = Overlay("/home/xilinx/jupyter_notebooks/dreams2.bit")
ol.download()

hdmi_in = ol.video.hdmi_in
hdmi_out = ol.video.hdmi_out


# In[2]:


vierkantje = MMIO(0x43C80000,0x10000)
xywh = (50,50,25,25)
#port x
vierkantje.write(0x10,xywh[0])
#port y
vierkantje.write(0x18,xywh[1])
#port w
vierkantje.write(0x20,xywh[2])
#port h
vierkantje.write(0x28,xywh[3])


# In[7]:


#port h
vierkantje.write(0x30,0)


# In[5]:


hdmi_in.configure(PIXEL_RGBA)
hdmi_out.configure(hdmi_in.mode, PIXEL_RGBA)

hdmi_in.start()
hdmi_out.start()


# In[4]:


import PIL.Image
frame = hdmi_in.readframe()
img = PIL.Image.fromarray(frame)
img.save("/home/xilinx/jupyter_notebooks/base/video/data/face_detect.jpg")

img


# In[6]:


hdmi_in.tie(hdmi_out)


# In[ ]:


hdmi_out.close()
hdmi_in.close()


# In[8]:


add_ip = MMIO(0x43C00000,0x10000)

#port a
add_ip.write(0x10,7)
print("add a:",add_ip.read(0x10))
#port b
add_ip.write(0x18,12)
print("add b:",add_ip.read(0x18))

#ap_start bit
add_ip.write(0x00,1)
#port y
print("add y:",add_ip.read(0x20))

