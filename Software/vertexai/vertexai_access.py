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
        payload = json.dumps({"action_call" :"generate_reponse","text_input": text_input, "image_input": image_input})
        response = requests.post(self.url, data=payload, headers=self.headers)
        return response.text
    
    def generate_embeddings(self,texts, task='RETRIEVAL_DOCUMENT'):
        """
        Send a list of texts to a remote server to generate embeddings for a specified task.
        
        Args:
            texts (list of str): The list of text documents for which embeddings are to be generated.
            task (str): The task type for which the embeddings are generated. Default is 'RETRIEVAL_DOCUMENT'.
        
        Returns:
            dict: A dictionary containing the server's response.
            
        Raises:
            requests.exceptions.RequestException: If the request fails for any connectivity issues.
            Exception: If any other unforeseen error occurs during request handling.
        """
        # Define the payload as a JSON string
        payload = json.dumps({
            "action_call": "generate_embeddings",
            "texts": texts,
            "task": task
        })


        # Send the request and catch exceptions related to connection issues
        try:
            response = requests.post(self.url, data=payload, headers=self.headers)
            response.raise_for_status()  # Raises an HTTPError for bad responses
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            raise
        
        # Load and return the JSON response
        try:
            out = json.loads(response.text)
            return out
        except json.JSONDecodeError:
            raise Exception("Failed to decode the response from the server.")


# Example usage
if __name__ == "__main__":
    vertex_ai = VertexaiAccess('https://asia-south1-indigo-bazaar-420408.cloudfunctions.net/openvertex_tesrun')
    text_input = ["what is the text on the bottle and what is name of brand?"]
    image_path = "/content/1.jpg"
    response = vertex_ai.send_query(text_input, image_path)
    print(response)
