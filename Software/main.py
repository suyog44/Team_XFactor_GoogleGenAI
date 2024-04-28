#!/usr/bin/python3
"""
File : Main file for Trinetra Application
Author: Suyog Buradkar, Pramod Geddam
Date: 25 April 2024
"""

import time
import tempfile
import board
import busio
import adafruit_mpr121
from vertexai_access import VertexaiAccess
from alloydb_access import AlloydbAccess
from library.camera import Camera
from library.audio import AudioRecorder
from library.utils import get_last_session_id, save_session_id, increment_session_id
from google.cloud import texttospeech


SESSION_FILE_PATH = "/content/session.log"

def main():
    # Read last session ID or generate new one
    last_session_id = get_last_session_id()
    if last_session_id:
        session_id = last_session_id
    else:
        session_id = "session#00001"  # Initial session ID

    # Initialize MPR121
    i2c = busio.I2C(board.SCL, board.SDA)
    mpr121 = adafruit_mpr121.MPR121(i2c)

    # Vertex APIs initialization
    vertexai_url = 'https://asia-south1-hackathon-genai-08032024.cloudfunctions.net/vertexai_gen'
    alloydb_url = 'https://asia-south1-hackathon-genai-08032024.cloudfunctions.net/alloydb_connect'
    vertexai_ = VertexaiAccess(vertexai_url)
    db_access = AlloydbAccess(alloydb_url)

    TABLE_NAME = "learner_demo"

    # Text to Speech Setup
    speech_gen_client = texttospeech.TextToSpeechClient()

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Studio-O",
    )

    audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=1
    )

    while True:
        if mpr121[0].value:
            image_id = int(time.time())
            image_path = f"/content/Image_{image_id}.jpg"
            capture_image(image_path)
            encoded_image = db_access.encode_image_to_base64(image_path)
            response = vertexai_.send_query(["What is this image about?"], [image_path])
            print(response)
            embeds = vertexai_.generate_embeddings([response], task='RETRIEVAL_DOCUMENT')
            print(db_access.update_table(TABLE_NAME, session_id, encoded_image, response , embeds[0]))

        elif mpr121[2].value:
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

                audio_response = speech_gen_client.synthesize_speech(
                        request={"input": response, "voice": voice, "audio_config": audio_config}
                )

                # The response's audio_content is binary.
                with open("output.mp3", "wb") as out:
                    out.write(audio_response.audio_content)
                    print('Audio content written to file "output.mp3"')

        elif mpr121[3].value:
            # Generate new session ID
            session_id = increment_session_id(session_id)
            save_session_id(session_id)
            print("New session ID:", session_id)

        time.sleep(0.1) # Adjust delay as needed

if __name__ == "__main__":
    main()
