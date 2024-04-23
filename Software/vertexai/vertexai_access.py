import requests
import json
import base64

class VertexaiAccess:
    """
    This class provides methods to interact with a Vertex AI-based service via HTTP requests.
    It includes functionalities to encode images and send data for processing.
    """
    def __init__(self, url):
        """
        Initializes the VertexaiAccess object with the specified URL.

        Args:
        url (str): The URL of the Vertex AI service endpoint.
        """
        self.url = url
        self.headers = {'Content-Type': 'application/json'}

    @staticmethod
    def encode_image_to_base64(image_path):
        """
        Encodes an image file to a base64 string, suitable for JSON transmission.

        Args:
        image_path (str): Path to the image file to encode.

        Returns:
        str: A base64-encoded string of the image data.
        """
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string

    def send_query(self, text_input, image_paths):
        """
        Sends a query to the Vertex AI service along with an encoded image.

        Args:
        text_input (list of str): A list containing text queries.
        image_paths (list of str): Path to the image file to be processed.

        Returns:
        str: The response text from the Vertex AI service.
        """
        image_input = [self.encode_image_to_base64(image_path) for image_path in image_paths]
        payload = json.dumps({"text_input": text_input, "image_input": image_input})
        response = requests.post(self.url, data=payload, headers=self.headers)
        return response.text

# Example usage
if __name__ == "__main__":
    vertex_ai = VertexaiAccess('https://asia-south1-indigo-bazaar-420408.cloudfunctions.net/openvertex_tesrun')
    text_input = ["what is the text on the bottle and what is name of brand?"]
    image_path = "/content/1.jpg"
    response = vertex_ai.send_query(text_input, image_path)
    print(response)
