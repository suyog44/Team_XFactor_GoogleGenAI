#!/usr/bin/python3
"""
 *
 *  Unit code for Camera Recording & Save images
 *  with button clicks.
 *  Copyright: suyogburadkar@gmail.com
 *  Author: B Suyog
 *  Date: 14th April 2024
 *
"""

from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder
import time
from datetime import datetime
from gpiozero import Button
from signal import pause

picam2 = Picamera2()
button = Button(17)
button2 = Button(22)

def capture():
    print("Capture button pressed !! Capturing image !")
    camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (1280, 720)}, display="lores")
    picam2.configure(camera_config)
    picam2.set_controls({"AfMode": 2 ,"AfTrigger": 0})  # Continous Autofocus Added
    timestamp = datetime.now().isoformat()
    picam2.start()
    time.sleep(2) 
    picam2.capture_file('/home/pi/data/%s.jpg' % timestamp)
    print('Image saved successfully !!!!')
    picam2.stop_preview()
    picam2.stop()

def record():
    print("Record button pressed !! Starting video record !")
    video_config = picam2.create_video_configuration()
    picam2.configure(video_config)
    picam2.set_controls({"AfMode": 2 ,"AfTrigger": 0}) # Continous Autofocus Added
    timestp = datetime.now().isoformat()
    encoder = H264Encoder(10000000)
    picam2.start_recording(encoder, '/home/pi/data/%s.h264' % timestp)
    time.sleep(10)
    print("Video saved successfully !!!")
    picam2.stop_recording()

button.when_pressed = capture
button2.when_pressed = record
pause()
