#!/usr/bin/python3
"""
File: Touch button audio recording for LLM Chatbot
Date: 18th April 2024
Author: Suyog B
"""

import pyaudio
import board
import busio
import adafruit_mpr121 as MPR121
import wave

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Create I2C bus and MPR121 object
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = MPR121.MPR121(i2c)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Recording flag and previous button state
recording = False
prev_button_state = False

# Wave file object (initially None)
wf = None

def callback(in_data, frame_count, time_info, status):
    if recording:
        wf.writeframes(in_data)
    return (in_data, pyaudio.paContinue)

# Start streaming
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callback)

print("Press button 0 to start/stop recording")

while True:
    # Check for button presses and state change
    button_state = mpr121[0].value
    if button_state and not prev_button_state:  # Rising edge detected
        if not recording:
            print("Recording started")
            recording = True
            wf = wave.open('/home/pi/database/recording.wav', 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
        else:
            print("Recording stopped")
            recording = False
            wf.close()
            wf = None
    prev_button_state = button_state  # Update previous button state

# Stop stream and terminate PyAudio
stream.stop_stream()
stream.close()
p.terminate()
