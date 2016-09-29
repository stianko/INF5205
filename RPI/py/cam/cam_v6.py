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
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=10)


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
      label = myfont.render(str(s), 1, (255,255,255))
      
      screen.blit(label,( 0, 0))
      pygame.display.flip()
  except IndexError:
    print "End"

#Change last value if you want to be able to take more pictures  
def mapValue(value):
    return value/(1023/20)

def mapCities(value):
  return value/(1023/len(cities))

cities = [
  "    Oslo   ",
  "   Asker   ",
  "  Drammen  ",
  "Holmestrand",
  " Tonsberg  ",
  " Sandefjord",
  " Porsgrunn ",
  "  Arendal  ",
  "  Grimstad ",
  "Kristiansand"
  ]

#rotate image
def rotate(img):
  rImg = pygame.transform.rotate(img, 180)
#show image
def showImg(img):
  rImg = pygame.transform.rotate(img, 180)
  screen.blit(rImg,
        ((320 - img.get_width() ) / 2,
         (240 - img.get_height()) / 2))
def writeCities(value):
  label = myfont.render(cities[value], 1, (255,255,255))
  rLabel = pygame.transform.rotate(label, 180)
  screen.blit(rLabel, (80,40))
def writeSign(value):
  
  rSign = pygame.transform.rotate(sign, 180)
  screen.blit(rSign,
        ((320 - rSign.get_width() ) / 2,
         (240 - rSign.get_height()) / 2))
  label = myfont.render(cities[value], 1, (255,255,255))
  screen.blit(label, (80,180))
  


# Main loop ----------------------------------------------------------------
count = 0
tmp = 0
sim = 0
background_surface = pygame.image.load('img2.jpg')
sign = pygame.image.load('skilt.png')
scaled = None

#make a list of images
images = []

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

  tripCycle(s)    
  
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
  
      




