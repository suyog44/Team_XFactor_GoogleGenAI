#!/usr/bin/python3
"""
FILE: Goggle Working Code V1.3
DATE: 26th April 2024

"""
import time
import tempfile
from picamera2 import Picamera2
from libcamera import controls
import board
import busio
#import adafruit_mpr121
from gpiozero import Button
from google.cloud import speech_v1p1beta1 as speech
#from google.cloud import texttospeech
import pyaudio
import wave
import requests
import json
import base64
from gtts import gTTS
import pygame
import os

# Initialize Pygame (only once)
pygame.init()

from vertexai.vertexai_access import VertexaiAccess
from vertexai.alloydb_access import AlloydbAccess

from annoy import AnnoyIndex

SESSION_FILE_PATH = "/content/session.log"
#os.environ['GOOGLE_APPLICATION_CREDENTIALS']="hackathon-genai-08032024-a25af6b6e93f.json"

def speak(text):
    tts = gTTS(text=text, lang="en")
    tts.save("temp.mp3")
    pygame.mixer.music.load("temp.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()  # Stop music after playback
    os.remove("temp.mp3")

def get_last_session_id():
    try:
        with open(SESSION_FILE_PATH, "r") as file:
            last_session_id = file.read().strip()
        return last_session_id
    except FileNotFoundError:
        return None

def save_session_id(session_id):
    with open(SESSION_FILE_PATH, "w") as file:
        file.write(session_id)

def increment_session_id(session_id):
    session_number = int(session_id.split("#")[1])
    next_session_number = session_number + 1
    return f"session#{next_session_number:05d}"

# Read last session ID or generate new one
last_session_id = get_last_session_id()
if last_session_id:
    session_id = last_session_id
else:
    session_id = "session#00001"  # Initial session ID

speak("Welcome to Trinetra - Your personalized learning assistant")
# Print Active Session
print("Session ID: {}", session_id)
speak("Your current session id is")
speak(session_id)
# Initialize MPR121
#i2c = busio.I2C(board.SCL, board.SDA)
#mpr121 = adafruit_mpr121.MPR121(i2c)

#button initialize
button1 = Button(17)
button2 = Button(27)
button3 = Button(22)


# Camera and other initializations
picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (1280, 720)}, display="lores")
picam2.configure(camera_config)
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

# Vertex APIs initialization
vertexai_url = 'https://asia-south1-hackathon-genai-08032024.cloudfunctions.net/vertexai_gen'
alloydb_url = 'https://asia-south1-hackathon-genai-08032024.cloudfunctions.net/alloydb_connect'
vertexai_ = VertexaiAccess(vertexai_url)
db_access = AlloydbAccess(alloydb_url)

TABLE_NAME = "learner_demo"

image_captured = False

index = AnnoyIndex(768, 'angular')  # Using angular distance

# Create Text-to-Speech client using the credentials object
#speech_gen_client = texttospeech.TextToSpeechClient()

# Note: the voice can also be specified by name.
# Names of voices can be retrieved with client.list_voices().
#voice = texttospeech.VoiceSelectionParams(
#    language_code="en-US",
#    name="en-US-Studio-O",
#)

#audio_config = texttospeech.AudioConfig(
#    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
#    speaking_rate=1
#)

def capture_image(image_path):
    picam2.start()
    picam2.capture_file(image_path)
    print(f"Image captured and saved at: {image_path}")
    speak("Image saved successfully")
    image_captured = True

def transcribe_audio(audio_file_path):
    client = speech.SpeechClient.from_service_account_file('test/key.json')

    with open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        print("Transcript:", result.alternatives[0].transcript)
        return result.alternatives[0].transcript

def record_audio(audio_file_path, record_seconds=10):
    speak("Tell me your query")
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording...")

    frames = []
    for i in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(audio_file_path, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

# Main loop
while True:
    if button1.is_pressed:
        image_id = int(time.time())
        image_path = f"/content/Image_{image_id}.jpg"
        capture_image(image_path)
        encoded_image = db_access.encode_image_to_base64(image_path)
        response = vertexai_.send_query(["What is this image about?"], [image_path])
        print(response)
        embeds = vertexai_.generate_embeddings([response], task='RETRIEVAL_DOCUMENT')
        print(db_access.update_table(TABLE_NAME, session_id, encoded_image, response , embeds[0]))
        speak("Data saved to Google Cloud")

   # elif button2.is_pressed:
       # print("Video Recording is not available")

    elif button2.is_pressed:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
            audio_file_path = audio_file.name
            record_audio(audio_file_path)

        text_input = transcribe_audio(audio_file_path)

        if text_input:
            stored_data = db_access.retrieve_session_data(session_id , TABLE_NAME)
            embeds = stored_data["embedding"]

            for i in range(len(embeds)):
                embed = json.loads(embeds[i])
                index.add_item(i, embed)
            index.build(len(embeds) + 5)  # +5 trees

            query_embed = vertexai_.generate_embeddings([text_input], task='RETRIEVAL_QUERY')
            data_index = index.get_nns_by_vector(query_embed[0], 2, include_distances=True)

            data = "\n".join([stored_data["image_description"][index] for index in data_index[0] ])

            print("Data Retrieve ", data)

            prompt = f"Based on the context delimited in backticks, answer the query. ```{data}``` {text_input}"
            response = vertexai_.send_query([prompt], [])

            print("----------------------------------------------------------------------------------")

            print("----------------------------------------------------------------------------------")

            print("Response is: ")

            print(response)
            speak(response)

            index = AnnoyIndex(768, 'angular')  # Using angular distance

            #audio_response = speech_gen_client.synthesize_speech(
            #    request={"input": response, "voice": voice, "audio_config": audio_config}
            #)

            # The response's audio_content is binary.
            #with open("output.mp3", "wb") as out:
            #    out.write(audio_response.audio_content)
            #    print('Audio content written to file "output.mp3"')

    elif button3.is_pressed:
        # Generate new session ID
        session_id = increment_session_id(session_id)
        save_session_id(session_id)
        print("New session ID:", session_id)
        speak("New session id is")
        speak(session_id)

    time.sleep(0.5) # Adjust delay as needed
