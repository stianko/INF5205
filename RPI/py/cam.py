import picamera
import time
import Image

start_time =time.time()


camera = picamera.PiCamera()

camera.start_preview()

test = camera.capture('%s.jpg' % time.time())

img = Image.open(test)

time.sleep(5)

camera.capture('%s.jpg' % time.time())

camera.stop_preview()

# print img.format, img.size, img.mode
img.show()
