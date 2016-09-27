import serial

ser = serial.Serial('/dev/ttyACM0',115200)
s = [0,1]
while True:
  read=ser.readline()
  s = map(float,read.split(","))
  time = s[0]
  pot = s[1]
  
  print ('Time')
  print (time)
  print ('Position')
  print (pot)
  print ('Diff')
  print (pot/time)
