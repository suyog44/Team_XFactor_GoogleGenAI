import json
import requests
import base64

class AlloydbAccess:
    """
    This class provides methods to interact with a remote AlloyDB database via HTTP requests.
    It includes functionalities to create tables, update them, reindex, and retrieve data.
    """
    def __init__(self, url):
        self.url = url
        self.headers = {'Content-Type': 'application/json'}

    def create_table(self, table_name, sql_text):
        """
        Creates a table in the AlloyDB database.

        Args:
        table_name (str): Name of the table to be created.
        sql_text (str): SQL string defining the columns and types for the new table.
        """
        payload = json.dumps({"action_call": ['CREATE_TABLE', {'TABLE_NAME': table_name, 'sql_text': sql_text}]})
        response = requests.post(self.url, data=payload, headers=self.headers)
        return response.text

    def update_table(self, table_name, session_id, image_data, image_description , embeds = None):
        """
        Adds information to a specified table.

        Args:
        table_name (str): Name of the table to update.
        session_id (str): Session ID associated with the entry.
        image_data (str): Base64 encoded image data.
        image_description (str): Description of the image.
        """
        parameter_map = [{'session_id': session_id, 'image_data': image_data, 'image_description': image_description , 'embedding' : json.dumps(embeds)}]
        payload = json.dumps({"action_call": ['UPDATE_TABLE', {'TABLE_NAME': table_name, 'sql_text': '(:session_id, :image_data, :image_description , :embedding)', 'parameter_map': parameter_map}]})
        response = requests.post(self.url, data=payload, headers=self.headers)
        return response.text

    def reindex_table(self, table_name):
        """
        Reindexes a specified table.

        Args:
        table_name (str): Name of the table to reindex.
        """
        payload = json.dumps({"action_call": ['RECALCULATE_THE_INDEX', {'TABLE_NAME': table_name}]})
        response = requests.post(self.url, data=payload, headers=self.headers)
        return response.text

    def retrieve_from_table(self, table_name, query, row_count , sel_columns):
        """
        Retrieves rows from the table based on an embedding query.

        Args:
        table_name (str): Name of the table to retrieve data from.
        query (str): Query to match against embeddings.
        row_count (int): Maximum number of rows to retrieve.
        sel_columns (str): columns you want your data from . eg. 'session_id, image_data, image_description'
        """
        payload = json.dumps({"action_call": ['RETRIEVE_FROM_TABLE_EMBEDDING', {'TABLE_NAME': table_name, 'sel_columns': sel_columns, 'query': query, 'row_count': row_count}]})
        response = requests.post(self.url, data=payload, headers=self.headers)

        data_list= response.text.split(" __splitKey__ ")
        final_response = f"".join(data_list[::2])

        return final_response
    
        
    def retrieve_session_data(self,session_id , TABLE_NAME):
        """
        Sends a request to retrieve specific columns from a table in a database based on a session ID.
        
        Args:
            session_id (str): The session ID to filter the data retrieval.
        
        Returns:
            str: The response text from the server, which includes the retrieved data.
            
        Raises:
            requests.exceptions.RequestException: If the request fails due to connectivity issues or server errors.
            Exception: If any other unforeseen error occurs during request handling.
        """
        # Create the payload with the session_id and other parameters
        payload = json.dumps({
            "action_call": [
                'RETRIEVE_FROM_TABLE_SESSION',
                {
                    'TABLE_NAME': TABLE_NAME,
                    'sel_columns': 'image_data, image_description, embedding',
                    'sel_session': session_id
                }
            ]
        })
        
        
        # Execute the POST request and handle potential exceptions
        try:
            response = requests.post(self.url, data=payload, headers=self.headers)
            response.raise_for_status()  # Raises an HTTPError for bad responses
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
        
        # Return the text of the response
        return json.loads(response.text)


    @staticmethod
    def encode_image_to_base64(image_path):
        """
        Encodes an image file to a base64 string.

        Args:
        image_path (str): Path to the image file.
        """
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string

# Example usage
if __name__ == "__main__":
    db_access = AlloydbAccess('https://asia-south1-indigo-bazaar-420408.cloudfunctions.net/alloydb_connect')
    print(db_access.create_table(TABLE_Name, "(session_id VARCHAR, image_data TEXT, image_description TEXT)"))
    encoded_image = db_access.encode_image_to_base64("/content/1.jpeg")
    print(db_access.update_table(TABLE_Name, "Random_session_id", encoded_image, "My name is out"))
    print(db_access.reindex_table(TABLE_Name))
    print(db_access.retrieve_from_table(TABLE_Name, "what is name of brand?", 10))
