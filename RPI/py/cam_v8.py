#!/usr/bin/python
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
def tripCycle(s):
  try:
    if mapCities(pot) == cities[mapCities(pot)]:
      screen.fill(0)
      writeCities(mapCities(pot))
      pygame.display.flip()

    else:
      screen.fill(0)
      writeSign(mapCities(pot))
      writeCities(mapCities(pot))
      #label = myfont.render(str(s), 1, (255,255,255))
      
      #screen.blit(label,( 0, 0))
      pygame.display.flip()
  except IndexError:
    print "End"

#Change last value if you want to be able to take more pictures  
def mapValue(value):
    return value/(1023/25)

def mapCities(value):
  return value/(1023/len(cities))

cities = [
  "Oslo",
  "Asker",
  "Drammen",
  "Holmestrand",
  "Tonsberg",
  "Sandefjord",
  "Porsgrunn",
  "Arendal",
  "Grimstad",
  "Kristiansand"
  ]

#rotate image
def rotate(img):
  rImg = pygame.transform.rotate(img, 180)
#show image
def showImg(img):
  #rImg = pygame.transform.rotate(img, 180)
  screen.blit(img,
        ((320 - img.get_width() ) / 2,
         (240 - img.get_height()) / 2))
def writeCities(value):
  label = myfont.render(cities[value], 1, (255,255,255))
  rLabel = pygame.transform.rotate(label, 180)
  screen.blit(rLabel, (80,30))
def writeSign(value):
  
  rSign = pygame.transform.rotate(sign, 180)
  screen.blit(rSign,
        ((320 - rSign.get_width() ) / 2,
         (240 - rSign.get_height()) / 2))
  
  


# Main loop ----------------------------------------------------------------
count = 0
tmp = 0
sim = 0
background_surface = pygame.image.load('img2.jpg')
sign = pygame.image.load('skilt.png')
scaled = None

#make a list of images
images = []
imgArray = []

#scaled = pygame.image.load('img2.jpg')
#scaled = pygame.transform.scale(scaled, (320,240))
#print(scaled.get_height())
imgPot = 0
tmpImg = None
running = True
while(running):
  
  #read serial
  read=ser.readline()
  try:
    s = map(int, read.split(","))
  
    t = s[1]
    pot = s[0]

    diff = pot/t
  except ValueError:
    print "Ended"
  #print ('Time')
  #print (t)
  #print ('Position')
  #print (pot)
  #print ('Diff')
 # print (t / pot)

  
  #screen.blit(background_surface, (320,240))
  
  #print(input_state)
  if screenMode < 2: # Playback mode or delete confirmation
    img = scaled       # Show last-loaded image

  #if images is not None:
    
  try:
    if (mapValue(pot) in images):
    #if pot + 20 >= images.index(pot) or pot -20 <= images.index(pot):
    #if images is not None and imgPot < pot + 20 and imgPot > pot - 20 and (diff < 0.97):
      #screen.fill(0)
      imgName = str(mapValue(pot)) + '.jpg'
     
      #img = pygame.image.load(imgName)
      #callImg = pygame.transform.scale(imgName,(320, 240))
      showImg(imgArray[images.index(mapValue(pot))])
      writeSign(mapCities(pot))
      writeCities(mapCities(pot))
      
    
      pygame.display.flip()
      #print 'here now'
    else:
      tripCycle(s)
  except ValueError, IndexError:
    print "Didnt find pot value, not in array. Cycling through trip again."
    tripCycle(s) 
     


  #if((pot==0) or (pot==100) or (pot ==200) or (pot == 300) or (pot==400) or (pot==500) or (pot==600) or (pot==700) or (pot==800)):
   # screen.fill(0)
    #option[pot]()
      #screen.blit(img,
        #((320 - img.get_width() ) / 2,
         #(240 - img.get_height()) / 2))
    
    #pygame.display.flip()
  input_state = GPIO.input(21)
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
    input_state = GPIO.input(21)
    if (input_state == True):

      print('Button released')
      fileName = str(mapValue(t)) + '.jpg' 
      camera.capture(fileName)

      #Maybe need to load image later as well
      img = pygame.image.load(fileName)
      

      scaled = pygame.transform.scale(img,(320, 240))
      imgArray.append(scaled)
      imgPot = pot

      #append the image to list
      images.append(mapValue(t))

      #images.append(pot)
      #range(pot, pot+10, 1)
        
      
      print imgPot
      #running = False
      #input_state = True
      count = 0
      #break
      
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
      
print images
print imgArray
  
      




