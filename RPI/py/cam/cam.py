
import atexit
import cPickle as pickle
import errno
import fnmatch
import io
import os
import os.path
import picamera
import pygame
import stat
import threading
import time
import yuv2rgb
from pygame.locals import *
from subprocess import call  




screenMode      =  3      # Current screen mode; default = viewfinder
screenModePrior = -1      # Prior screen mode (for detecting changes)
settingMode     =  4      # Last-used settings mode (default = storage)
storeMode       =  0      # Storage mode; default = Photos folder
storeModePrior  = -1      # Prior storage mode (for detecting changes)
sizeMode        =  0      # Image size; default = Large
fxMode          =  0      # Image effect; default = Normal
isoMode         =  0      # ISO settingl default = Auto
iconPath        = 'icons' # Subdirectory containing UI bitmaps (PNG format)
saveIdx         = -1      # Image index for saving (-1 = none set yet)
loadIdx         = -1      # Image index for loading
scaled          = None    # pygame Surface w/last-loaded image



sizeData = [ # Camera parameters for different size settings
 # Full res      Viewfinder  Crop window
 [(2592, 1944), (320, 240), (0.0   , 0.0   , 1.0   , 1.0   )], # Large
 [(1920, 1080), (320, 180), (0.1296, 0.2222, 0.7408, 0.5556)], # Med
 [(1440, 1080), (320, 240), (0.2222, 0.2222, 0.5556, 0.5556)]] # Small

isoData = [ # Values for ISO settings [ISO value, indicator X position]
 [  0,  27], [100,  64], [200,  97], [320, 137],
 [400, 164], [500, 197], [640, 244], [800, 297]]

fxData = [
  'none', 'sketch', 'gpen', 'pastel', 'watercolor', 'oilpaint', 'hatch',
  'negative', 'colorswap', 'posterise', 'denoise', 'blur', 'film',
  'washedout', 'emboss', 'cartoon', 'solarize' ]


icons = [] # This list gets populated at startup

# buttons[] is a list of lists; each top-level list element corresponds
# to one screen mode (e.g. viewfinder, image playback, storage settings),
# and each element within those lists corresponds to one UI button.
# There's a little bit of repetition (e.g. prev/next buttons are
# declared for each settings screen, rather than a single reusable
# set); trying to reuse those few elements just made for an ugly
# tangle of code elsewhere.




# Initialization -----------------------------------------------------------

# Init framebuffer/touchscreen environment variables
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV'      , '/dev/fb1')
os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

# Get user & group IDs for file & folder creation
# (Want these to be 'pi' or other user, not root)
s = os.getenv("SUDO_UID")
uid = int(s) if s else os.getuid()
s = os.getenv("SUDO_GID")
gid = int(s) if s else os.getgid()

# Buffers for viewfinder data
rgb = bytearray(320 * 240 * 3)
yuv = bytearray(320 * 240 * 3 / 2)

# Init pygame and screen
pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)

# Init camera and set up default values
camera            = picamera.PiCamera()
atexit.register(camera.close)
camera.resolution = sizeData[sizeMode][1]
#camera.crop       = sizeData[sizeMode][2]
camera.crop       = (0.0, 0.0, 1.0, 1.0)
# Leave raw format at default YUV, don't touch, don't set to RGB!




# Main loop ----------------------------------------------------------------

while(True):

  # Process touchscreen input
  while True:
    for event in pygame.event.get():
      if(event.type is MOUSEBUTTONDOWN):
        pos = pygame.mouse.get_pos()
        
    # If in viewfinder or settings modes, stop processing touchscreen
    # and refresh the display to show the live preview.  In other modes
    # (image playback, etc.), stop and refresh the screen only when
    # screenMode changes.
    if screenMode >= 3 or screenMode != screenModePrior: break

  # Refresh display
  if screenMode >= 3: # Viewfinder or settings modes
    stream = io.BytesIO() # Capture into in-memory stream
    camera.capture(stream, use_video_port=True, format='raw')
    stream.seek(0)
    stream.readinto(yuv)  # stream -> YUV buffer
    stream.close()
    yuv2rgb.convert(yuv, rgb, sizeData[sizeMode][1][0],
      sizeData[sizeMode][1][1])
    img = pygame.image.frombuffer(rgb[0:
      (sizeData[sizeMode][1][0] * sizeData[sizeMode][1][1] * 3)],
      sizeData[sizeMode][1], 'RGB')
  elif screenMode < 2: # Playback mode or delete confirmation
    img = scaled       # Show last-loaded image
  else:                # 'No Photos' mode
    img = None         # You get nothing, good day sir

  if img is None or img.get_height() < 240: # Letterbox, clear background
    screen.fill(0)
  if img:
    screen.blit(img,
      ((320 - img.get_width() ) / 2,
       (240 - img.get_height()) / 2))

  # Overlay buttons on display and update
 
  pygame.display.update()

  screenModePrior = screenMode
