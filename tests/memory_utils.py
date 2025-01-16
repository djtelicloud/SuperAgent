from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import json
import asyncio
from azure.storage.blob import ContainerClient



# Load the memory data from a api in super_agent_memories.py
#port 8001

# @app.get('/memorydata', response_model=MemoryData)
# async def get_memory():
#     @app.put('/memorydata', response_model=MemoryData)
# async def update_memory(memory_data: MemoryData):
# import httpx
# url = "http://127.0.0.1:8001/api/memorydata"
# memory_storage = httpx.AsyncClient()
# from super_agent_memories import MemoryData, Memories

# async def get_memory_data():
#     json_data = memory_storage.get(url)
#     data = json_data.json()
#     return data

# async def update_memory_data(memory_data):
#     response = memory_storage.put(url, json=memory_data)
#     return response
    
    
# Define the connection string for your Azure Blob Storage
connection_string = "DefaultEndpointsProtocol=https;AccountName=centriadwstorageacctdev;AccountKey=HiF66jDHTjwuvBS4aZE6bZE7ppfu+HS7m41C8uRANPGq64aXnugl8XPQvINGUmclaLPT3ivPV4dGg/R/ZlKGcg==;EndpointSuffix=core.windows.net"

# Define a memory data structure
target_file = 'super_agent_memory.json'

# Initialize the container client
container_client = ContainerClient.from_connection_string(conn_str=connection_string, container_name="payergpt-container")

app = FastAPI()

class Memories(BaseModel):
    """
    Memories class to store and manage memory data.
    The data is stored and fetched as a single JSON object with
    'memories' and 'messages' as keys. The structure of the memory
    parameters can be customized as needed.

    Args:
        data (dict): The memory data.
        Default Attributes:
            memories (dict): The memories data.
            messages (dict): The messages data.
    Returns:
        Memories: The memory data object.
    """
    data: dict = Field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(data=data or {
            "memories": {},
            "messages": {}
        })

    def __str__(self):
        return json.dumps(self.data, indent=4)

    def __repr__(self):
        return str(self)
    
    def __getitem__(self, key):
        """
        Get the value associated with the given key.
        
        Args:
            key (str): The key to look up.
        
        Returns:
            The value associated with the key, or None if the key does not exist.
        """
        return self.data.get(key, None)
    
    def __setitem__(self, key, value):
        """
        Set the value for the given key.
        
        Args:
            key (str): The key to set.
            value: The value to associate with the key.
        """
        self.data[key] = value

    def __delitem__(self, key):
        """
        Delete the key-value pair associated with the given key.
        
        Args:
            key (str): The key to delete.
        """
        del self.data[key]

    def __contains__(self, key):
        """
        Check if the given key exists in the memory data.
        
        Args:
            key (str): The key to check.
        
        Returns:
            bool: True if the key exists, False otherwise.
        """
        return key in self.data
    
    def __iter__(self):
        """
        Iterate over the keys in the memory data.
        
        Returns:
            An iterator over the keys in the memory data.
        """
        return iter(self.data)
    
    def __len__(self):
        """
        Get the number of key-value pairs in the memory data.
        
        Returns:
            int: The number of key-value pairs.
        """
        return len(self.data)
    
    def __bool__(self):
        """
        Check if the memory data is non-empty.
        
        Returns:
            bool: True if the memory data is non-empty, False otherwise.
        """
        return bool(self.data)
    
    def __eq__(self, other):
        """
        Check if the memory data is equal to another memory data object.
        
        Args:
            other (Memories): The other memory data object to compare.
        
        Returns:
            bool: True if the memory data is equal, False otherwise.
        """
        return self.data == other.data
    
    def __ne__(self, other):
        """
        Check if the memory data is not equal to another memory data object.
        
        Args:
            other (Memories): The other memory data object to compare.
        
        Returns:
            bool: True if the memory data is not equal, False otherwise.
        """
        return self.data != other.data

    def get(self, key, default=None):
        """
        Get the value associated with the given key, or a default value if the key does not exist.
        
        Args:
            key (str): The key to look up.
            default: The default value to return if the key does not exist.
        
        Returns:
            The value associated with the key, or the default value.
        """
        return self.data.get(key, default)
    
    def set(self, key, value):
        """
        Set the value for the given key.
        
        Args:
            key (str): The key to set.
            value: The value to associate with the key.
        """
        self.data[key] = value
    
    def delete(self, key):
        """
        Delete the key-value pair associated with the given key.
        
        Args:
            key (str): The key to delete.
        """
        del self.data[key]
    
    def clear(self):
        """
        Clear all key-value pairs from the memory data.
        """
        self.data.clear()
    
    def keys(self):
        """
        Get a view of the keys in the memory data.
        
        Returns:
            A view of the keys in the memory data.
        """
        return self.data.keys()
    
    def values(self):
        """
        Get a view of the values in the memory data.
        
        Returns:
            A view of the values in the memory data.
        """
        return self.data.values()
    
    def items(self):
        """
        Get a view of the key-value pairs in the memory data.
        
        Returns:
            A view of the key-value pairs in the memory data.
        """
        return self.data.items()
    
    def update(self, other):
        """
        Update the memory data with key-value pairs from another memory data object.
        
        Args:
            other (Memories): The other memory data object to update from.
        """
        self.data.update(other.data)

    def pop(self, key, default=None):
        """
        Remove the key-value pair associated with the given key and return the value.
        
        Args:
            key (str): The key to remove.
            default: The default value to return if the key does not exist.
        
        Returns:
            The value associated with the key, or the default value.
        """
        return self.data.pop(key, default)
    
    def popitem(self):
        """
        Remove and return a key-value pair from the memory data.
        
        Returns:
            A tuple containing the key and value of the removed pair.
        """
        return self.data.popitem()
    
    def copy(self):
        """
        Create a shallow copy of the memory data.
        
        Returns:
            dict: A shallow copy of the memory data.
        """
        return self.data.copy()
    
    def to_dict(self):
        """
        Convert the memory data to a dictionary.
        
        Returns:
            dict: The memory data as a dictionary.
        """
        return self.data
    
    def from_dict(self, data):
        """
        Update the memory data from a dictionary.
        
        Args:
            data (dict): The dictionary to update from.
        """
        self.data = data
    
    def to_json(self):
        """
        Convert the memory data to a JSON string.
        
        Returns:
            str: The memory data as a JSON string.
        """
        return json.dumps(self.data)
    
    def from_json(self, json_data):
        """
        Update the memory data from a JSON string.
        
        Args:
            json_data (str): The JSON string to update from.
        """
        self.data = json.loads(json_data)

    
class MemoryData(BaseModel):
    data: dict

# Read full JSON from a file with timeout logic
async def read_json_file():
    """
    Reads the full JSON from the target file in Azure Blob Storage with a timeout of 20 seconds.
    If the operation takes longer than 20 seconds, returns an error message.

    Returns:
        dict: The content of the JSON file or an error message if the operation times out.

    Raises:
        HTTPException: If there is an error reading the file.
    """
    try:
        return await asyncio.wait_for(_read_json_file(), timeout=20)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out while reading the memory file.")

async def _read_json_file():
    """
    Helper function to read the JSON file from Azure Blob Storage.

    Returns:
        dict: The content of the JSON file.

    Raises:
        HTTPException: If there is an error reading the file.
    """
    try:
        blob_client = container_client.get_blob_client(target_file)
        download_stream = blob_client.download_blob()
        return json.loads(download_stream.readall())
    except Exception as e:
        if "BlobNotFound" in str(e):
            # Create an empty memory file if it does not exist
            empty_data = {"memories": {}, "messages": {}}
            await _write_json_file(empty_data)
            return empty_data
        raise HTTPException(status_code=500, detail=f"Failed to read memory file: {str(e)}")

# Save full JSON to a file with timeout and retry logic
async def write_json_file(data):
    """
    Saves the full JSON to the target file in Azure Blob Storage with a timeout of 10 seconds.
    If the operation takes longer than 10 seconds, pops the last message and retries.
    Continues this process until the save is successful or there are no more messages to pop.

    Args:
        data (dict): The data to be saved to the JSON file.

    Raises:
        HTTPException: If there is an error saving the file or if there are no messages to pop.
    """
    while True:
        try:
            await asyncio.wait_for(_write_json_file(data), timeout=10)
            break
        except asyncio.TimeoutError:
            if "messages" in data and data["messages"]:
                data["messages"].pop(-1)
            else:
                raise HTTPException(status_code=500, detail="Failed to save memory file: Timeout and no messages to pop")

async def _write_json_file(data):
    """
    Helper function to write the JSON file to Azure Blob Storage.

    Args:
        data (dict): The data to be saved to the JSON file.

    Raises:
        HTTPException: If there is an error saving the file.
    """
    try:
        blob_client = container_client.get_blob_client(target_file)
        blob_client.upload_blob(json.dumps(data), overwrite=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save memory file: {str(e)}")

@app.get('/memorydata', response_model=MemoryData)
async def get_memory():
    """
    API endpoint to get the memory data.

    Returns:
        MemoryData: The memory data.
    """
    try:
        data = await read_json_file()
        return MemoryData(data=data)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.put('/memorydata', response_model=MemoryData)
async def update_memory(memory_data: MemoryData):
    """
    API endpoint to update the memory data.

    Args:
        memory_data (MemoryData): The memory data to be updated.

    Returns:
        MemoryData: The updated memory data.
    """
    try:
        await write_json_file(memory_data.data)
        return memory_data
    
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Provide the API endpoint to run the FastAPI application
# This will allow the API to be accessed from the provided URL
# The API can be used to interact with the memory data
# The memory data is stored in an Azure Blob Storage container
# The API provides endpoints to read and update the memory data
# The memory data is in JSON format and can be accessed using the provided API
# The API uses asynchronous functions to handle read and write operations

# If name is main test
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)