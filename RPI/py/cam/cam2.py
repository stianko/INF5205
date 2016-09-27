import serial
import atexit
import Image
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

import RPi.GPIO as GPIO


#serial data
ser = serial.Serial('/dev/ttyACM0', 115200)


#The trigger button
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)

screenMode      =  1     # Current screen mode; default = viewfinder
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
myfont = pygame.font.SysFont("monospace", 30)

# Init camera and set up default values
camera            = picamera.PiCamera()
atexit.register(camera.close)
camera.resolution = sizeData[sizeMode][1]
#camera.crop       = sizeData[sizeMode][2]
camera.crop       = (0.0, 0.0, 1.0, 1.0)
# Leave raw format at default YUV, don't touch, don't set to RGB!

#switch case to simulate travel route


def oslo():
  label = myfont.render("Oslo", 1, (255,255,255))
  screen.blit(label, (100, 100))
def asker():
  label = myfont.render("Asker", 1, (255,255,255))
  screen.blit(label, (100, 100))
def drammen():
  label = myfont.render("Drammen", 1, (255,255,255))
  screen.blit(label, (100, 100))
def holmestrand():
  label = myfont.render("Holmestrand", 1, (255,255,255))
  screen.blit(label, (100, 100))
def tonsberg():
  label = myfont.render("Tonsberg", 1, (255,255,255))
  screen.blit(label, (100, 100))
def sandefjord():
  label = myfont.render("Sandefjord", 1, (255,255,255))
  screen.blit(label, (100, 100))
def porsgrunn():
  label = myfont.render("Porsgrunn", 1, (255,255,255))
  screen.blit(label, (100, 100))
def arendal():
  label = myfont.render("Arendal", 1, (255,255,255))
  screen.blit(label, (100, 100))
def kristiansand():
  label = myfont.render("Kristiansand", 1, (255,255,255))
  screen.blit(label, (100, 100))
  
option = {
  0 : oslo,
  100 : asker,
  200 : drammen,
  300 : holmestrand,
  400 : tonsberg,
  500 : sandefjord,
  600 : porsgrunn,
  700 : arendal,
  800 : kristiansand
}

# Main loop ----------------------------------------------------------------
count = 0
tmp = 0
sim = 0
background_surface = pygame.image.load('img2.jpg')
scaled = pygame.image.load('img2.jpg')
scaled = pygame.transform.scale(scaled, (320,240))
#print(scaled.get_height())
running = True
while(running):
  
  #read serial
  read=ser.readline()
  s = map(float,read.split(","))
  t = s[0]
  pot = s[1]

  diff = pot/t
  
  #print ('Time')
  #print (t)
  #print ('Position')
  #print (pot)
  #print ('Diff')
 # print (t / pot)

  
  #screen.blit(background_surface, (320,240))
  input_state = GPIO.input(21)
  #print(input_state)
  if screenMode < 2: # Playback mode or delete confirmation
    img = scaled       # Show last-loaded image

  #hard coded, ugly ugly code
  if(pot > 0.0 and pot < 99.0):
    print(pot)  
    screen.fill(0)
    oslo()
    print(pot)
    pygame.display.flip()
  elif(pot > 100.0 and pot < 199.0):
    screen.fill(0)
    asker()
    pygame.display.flip()
  elif(pot > 200.0 and pot < 299.0):
    screen.fill(0)
    drammen()
    pygame.display.flip()
  elif(pot > 300.0 and pot < 399.0):
    screen.fill(0)
    holmestrand()
    pygame.display.flip()
  elif(pot > 400.0 and pot < 499.0):
    screen.fill(0)
    tonsberg()
    pygame.display.flip()
  elif(pot > 500.0 and pot < 599.0):
    screen.fill(0)
    sandefjord()
    pygame.display.flip()
  elif(pot > 600.0 and pot < 699.0):
    screen.fill(0)
    porsgrunn()
    pygame.display.flip()
  elif(pot > 700.0 and pot < 799.0):
    screen.fill(0)
    arendal()
    pygame.display.flip()
  else:
    screen.fill(0)
    kristiansand()
    pygame.display.flip()
  

  #if((pot==0) or (pot==100) or (pot ==200) or (pot == 300) or (pot==400) or (pot==500) or (pot==600) or (pot==700) or (pot==800)):
   # screen.fill(0)
    #option[pot]()
      #screen.blit(img,
        #((320 - img.get_width() ) / 2,
         #(240 - img.get_height()) / 2))
    
    #pygame.display.flip()
  while(input_state == False):
    screenMode = 3
    
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
      #print(img.get_height())
    else:              # 'No Photos' mode
      img = None         # You get nothing, good day sir

    if img is None: # Letterbox, clear background
      screen.fill(0)
    if img:
      screen.blit(img,
        ((320 - img.get_width() ) / 2,
         (240 - img.get_height()) / 2))
      
      #tmp = tmp + 1;
      #if (tmp > 50):
      #  screenMode = 3
           

    # Overlay buttons on display and update
      
    print('Button pressed!')
    #print(input_state)
    #camera.capture('%s.jpg' % time.time())
    
    pygame.display.update()

  
    screenModePrior = screenMode
    count = count + 1
    if (count > 50):
      running = False
      break
  for event in pygame.event.get():
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        running = False
        break
      elif event.type == pygame.QUIT:
        running = False
        break
      if not running:
        break
      
  
  
      


print('Button released')
camera.capture('%s.jpg' % time.time())

