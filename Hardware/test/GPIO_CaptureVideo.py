#!/usr/bin/python3

import time
from gpiozero import Button
from signal import pause
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder

picam2 = Picamera2()
button = Button(22)

video_config = picam2.create_video_configuration()
picam2.configure(video_config)

def record_video():
    print("Recording video...")
    encoder = H264Encoder(10000000)
    picam2.start_recording(encoder, '/home/pi/data/test.h264')
    time.sleep(10)  # Adjust the duration as needed
    print('Video saved successfully.........')
    picam2.stop_recording()

button.when_pressed = record_video
pause()
