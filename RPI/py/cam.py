import picamera
import time
import Image

start_time =time.time()


camera = picamera.PiCamera()

camera.start_preview()

camera.capture('%s.jpg' % time.time())



time.sleep(5)

camera.capture('%s.jpg' % time.time())

camera.stop_preview()

# print img.format, img.size, img.mode
img.show()
