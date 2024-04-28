"""
File : Camera system for capture session
Author: Suyog Buradkar
Date: 25 April 2024
"""

from picamera2 import Picamera2
from libcamera import controls

picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (1280, 720)}, display="lores")
picam2.configure(camera_config)
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

def capture_image(image_path):
    picam2.start()
    picam2.capture_file(image_path)
    print(f"Image captured and saved at: {image_path}")
