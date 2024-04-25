#!/usr/bin/python3
"""
FILE: Goggle Working Code V1.0
DATE: 18th April 2024

"""
import time
import tempfile
from picamera2 import Picamera2
from libcamera import controls
import board
import busio
import adafruit_mpr121
from google.cloud import speech_v1p1beta1 as speech
import pyaudio
import wave
import requests
import json
import base64

from vertexai.vertexai_access import VertexaiAccess
from vertexai.alloydb_access import AlloydbAccess

from annoy import AnnoyIndex


# LLM Function
# def encode_image_to_base64(image_path):
#     with open(image_path, "rb") as image_file:
#         encoded_string = base64.b64encode(image_file.read())
#         encoded_string = encoded_string.decode('utf-8')
#     return encoded_string

# def call_llm_api(text_input, image_path=None):
#     if image_path:
#         encoded_image = encode_image_to_base64(image_path)
#         payload = json.dumps({"text_input": text_input, "image_input": [encoded_image]})
#     else:
#         payload = json.dumps({"text_input": text_input})

#     url = 'https://asia-south1-indigo-bazaar-420408.cloudfunctions.net/openvertex_tesrun'
#     headers = {'Content-Type': 'application/json'}

#     response = requests.post(url, data=payload, headers=headers)
#     print(response.text)

# Speech-to-Text and Audio Recording Functions
def transcribe_audio(audio_file_path):
    #client = speech.SpeechClient()
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

# Camera and MPR121 Initialization
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)
picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (1280, 720)}, display="lores")
picam2.configure(camera_config)
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

# Vertex apis intialization 
vertexai_url = 'https://asia-south1-indigo-bazaar-420408.cloudfunctions.net/openvertex_tesrun'
alloydb_url = 'https://asia-south1-indigo-bazaar-420408.cloudfunctions.net/alloydb_connect'
vertexai_ = VertexaiAccess(vertexai_url)
db_access = AlloydbAccess(alloydb_url)

TABLE_Name = "late_night_tests"
# print(db_access.create_table(TABLE_Name , '(session_id VARCHAR , image_data TEXT ,image_description TEXT)'))

image_captured = False

session_id =  "122312121" #"seret"

index = AnnoyIndex(768, 'angular')  # Using angular distance


# Function to capture image with unique ID
def capture_image(image_path):
    picam2.start()
    picam2.capture_file(image_path)
    print(f"Image captured and saved at: {image_path}")
    image_captured = True


# Function to record video for 10 seconds
def record_video():
    video_path = f"/content/video_{int(time.time())}.h264"
    picam2.start_recording(video_path)
    time.sleep(10)
    picam2.stop_recording()
    print(f"Video recorded and saved at: {video_path}")

def prompt_creator(data , query):

    prompt = """You are a friendly advisor helping to answer questions. Based on the search request we have loaded a list of documents closely related to the search.

        The user asked:
        <question>
        {query}
        </question>

        Here is the list of matching documents:
        <roles>
        {data}
        </roles>

        You should answer the question using the matching documents, reply with supplemental information.
        Answer:
        """
    
    return prompt
    


# Main loop
while True:
    # Check for touched electrodes
    if mpr121[0].value:
        image_id = int(time.time())
        image_path = f"/content/Image_{image_id}.jpg"
        capture_image(image_path)
        encoded_image = db_access.encode_image_to_base64(image_path)
        response = vertexai_.send_query(["What is this image about?"], [image_path])
        print(response)
        embeds = vertexai_.generate_embeddings([response], task='RETRIEVAL_DOCUMENT')
        print(db_access.update_table(TABLE_Name, session_id, encoded_image, response , embeds[0]))
        # print(db_access.reindex_table(TABLE_Name))
        #call_llm_api(["Analyze this image"], image_path)

    elif mpr121[1].value:
        #record_video()
        print("Video Recording is not available")
    elif mpr121[2].value:
        # Record audio temporarily
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
            audio_file_path = audio_file.name
            record_audio(audio_file_path)

        # Transcribe the audio
        text_input = transcribe_audio(audio_file_path)


        if text_input:

            stored_data = db_access.retrieve_session_data(session_id)
            embeds = stored_data["embedding"]

            print(len(embeds))

            for i in range(len(embeds)):
                embed = json.loads(embeds[i])
                print(len(embed))
                index.add_item(i, embed)
            index.build(10)  # 10 trees 

            query_embed = vertexai_.generate_embeddings([text_input], task='RETRIEVAL_QUERY')
            data_index = index.get_nns_by_vector(query_embed[0], 2, include_distances=True)

            data = "\n".join([stored_data["image_description"][index] for index in data_index[0] ])

            # data = db_access.retrieve_from_table(TABLE_Name, text_input, 2 , 'image_description')
            print("Data : " , data)

            prompt = prompt_creator(data , text_input)
            response = vertexai_.send_query([prompt], [])  # Call LLM with transcribed text
            print(response)

            # del index


    # if image_captured:
    #     print("")
    #     encoded_image = db_access.encode_image_to_base64(image_path)
    #     response = vertexai_.send_query(["What is this image about?"], [image_path])
    #     print(response)
    #     print(db_access.update_table(TABLE_Name, "122312121", encoded_image, response))
    #     print(db_access.reindex_table(TABLE_Name))
    #     image_captured = False

    time.sleep(0.1) # Adjust delay as needed
