import functions_framework

import base64
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models

def generate(input_set):
 
  model = GenerativeModel("gemini-1.5-pro-preview-0409")
  responses = model.generate_content(
      input_set,
      generation_config=generation_config,
      safety_settings=safety_settings,
      stream=True,
  )

  final_response = ""

  for response in responses:
    # print(response.text, end="")
    final_response += response.text

  return final_response

generation_config = {
    "max_output_tokens": 2000,
    "temperature": 1,
    "top_p": 0.95,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}


from typing import List

import vertexai
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

vertexai.init(project="hackathon-genai-08032024", location="asia-south1")

def embed_text(
    texts,
    task,
    model_name = "textembedding-gecko@003",
):
    """Embeds texts with a pre-trained, foundational model."""
    model = TextEmbeddingModel.from_pretrained(model_name)
    inputs = [TextEmbeddingInput(text, task) for text in texts]
    embeddings = model.get_embeddings(inputs)
    return [embedding.values for embedding in embeddings]

@functions_framework.http
def jarvis(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)

    if request_json:

        input_set = []
        
        # Load the JSON data
        data = request_json #json.loads(request_json)

        if "action_call" in data:
            action_call = data["action_call"]
        else:
            return "There is no action call in request"
        
        if action_call == "generate_reponse":

            if 'image_input' in data:
                for  base64_image in data["image_input"]:
                    # Decode the base64 string to binary
                    image_data = base64.b64decode(base64_image)
                    image = Part.from_data(
                        mime_type="image/jpeg",
                        data=image_data)
                    input_set.append(image)

            if 'text_input' in data:
                input_set.extend(data['text_input'])

            if len(input_set) ==0:
                return "Hi there! , there is no data in the request"

            final_response = generate(input_set)
            return final_response
        else:
            texts = data["texts"]
            task = data["task"]
            response = embed_text(texts,task)

            return json.dumps(response)
    
    else :
        return "Hi there! , there is no data in the request"
    
    # request_args = request.args

    # if request_json and 'name' in request_json:
    #     name = request_json['name']
    # elif request_args and 'name' in request_args:
    #     name = request_args['name']
    # else:
    #     name = 'World'
    # return 'Hello {}!'.format(name)

