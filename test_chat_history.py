import asyncio
import os
import json
import logging
from pydantic_ai.result import RunResult
import requests
import subprocess
import time


from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncAzureOpenAI
from pydantic import BaseModel
import os
import asyncio

import requests
import json

from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncAzureOpenAI
from pydantic import BaseModel
import os
import asyncio
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2024-06-01"
os.environ["OPENAI_API_BASE"] = "https://centriaopenaidev.openai.azure.com/"
os.environ["OPENAI_API_KEY"] = "c1b675b6e1344180a583cfaa4d1b1b7d"  # Replace with secure value or Key Vault
os.environ["OPENAI_API_DEPLOYMENT"] = "gpt-4o"

async_client = AsyncAzureOpenAI(
    api_key=os.getenv(key="OPENAI_API_KEY") or "",
    api_version=os.getenv(key="OPENAI_API_VERSION") or "",
    azure_endpoint=os.getenv(key="OPENAI_API_BASE") or "",
    azure_deployment=os.getenv(key="OPENAI_API_DEPLOYMENT") or "",
    _strict_response_validation=True,
)
openai_model = OpenAIModel(
    model_name=os.getenv(key="OPENAI_API_DEPLOYMENT") or "gpt-4o",
    openai_client=async_client,
)
from openai import AzureOpenAI
client = AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  
    api_version="2024-02-01",
    azure_endpoint=os.getenv("OPENAI_API_BASE") or ""
)
with open('requirements.txt', 'r') as file:
    requirements = file.read()

SYSTEM_PROMPT = """
You are an expert coding agent.
Python packages:
{requirements}

You are talking to a user who is asking you to generate a new conversation history.
You will generate a new question, category and answer based on using these python packages.
The context is a python based coding agent that is helping the user with their coding needs.
When there is a new question, category and answer, you will store it in the database.
Some of the questions should mimic a real question but some should actually be
errors in the code that you recommend fixs for given the context.
The questions should be related to running shell commands but with chains of thought
about running env checks first to gather context before running the shell commands.
Then the agent will run the shell commands and return the results.
"""

from pydantic import Field

class ResponseClass(BaseModel):
    QUESTION: str = Field(
        alias="question", 
        description="The question asked by the parent.")
    CATEGORY: str = Field(
        alias="category",
        description="The category of the question.")
    
    ANSWER: str = Field(
        alias="answer",
        description="The answer to the question by you.")
    
 

from pydantic_ai import Agent

superAgent = Agent(
    model=openai_model,
    name="SuperAgent",
    system_prompt=SYSTEM_PROMPT,
    result_type=ResponseClass,
    #deps_type=InputClass,
    retries=3,
    model_settings={"temperature": 0.0},
    tools=[]

)



api_url = "http://localhost:8000"

async def run_tests():
    """Run a series of tests to verify functionality."""
    test_email = "test3@example.com"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    messages = []  # Initialize the messages list

    # Test 1: Store a message
    store_payload = {
        "user_email": test_email,
        "question": "Generate new conversation history",
        "category": "General",
        "answer": "Initial test answer"
    }
    history_request: requests.Response = requests.post(f"{api_url}/store", json=store_payload, headers=headers)
    print("Store Response:", history_request.text)  # Log the raw response text
    try:
        messages_json = history_request.json()
        for message in messages_json.get("results", []):
            messages.append({"question": message['question'], "category": message['category'], "answer": message['answer']})
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Parse Error in Store Test: {e}")

    message_count = 0
    messages = []

    while message_count < 2:
        fag_prompt = f"{messages}\nGenerate new conversation history"
        faqs: RunResult[ResponseClass] = await superAgent.run(user_prompt=fag_prompt)
        messages.append({"question": faqs.data.QUESTION, "category": faqs.data.CATEGORY, "answer": faqs.data.ANSWER})
        store_payload['question'] = faqs.data.QUESTION
        store_payload['category'] = faqs.data.CATEGORY
        store_payload['answer'] = faqs.data.ANSWER
        response: requests.Response = requests.post(f"{api_url}/store", json=store_payload, headers=headers)
        print("Store Response:", response.text)  # Log the raw response text
        try:
            store_result = response.json()
            print("Parsed JSON:", json.dumps(store_result, indent=4))
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON Parse Error in Store Test {message_count}: {e}")
        message_count += 1
        
        print(f"\n=== Store Test {message_count} Results ===")
        try:
            store_result = response.json()
            print("Parsed JSON:", json.dumps(store_result, indent=4))
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
    
        # Test 2: Summarize a message
        store_payload2 = {
            "user_email": test_email,
            "question":  response.json().get('message', '')
        }

        print("\n=== Summarize Test Results ===")
        response2: requests.Response = requests.post(f"{api_url}/summarize", json=store_payload2, headers=headers)
        print("Summarize Response:", response2.text)  # Log the raw response text
        try:
            store_payload['question'] = response2.json().get('enhanced_question', '')
            response3: requests.Response = requests.post(f"{api_url}/store", json=store_payload, headers=headers)
            print("Store Response:", response3.text)  # Log the raw response text
            store_result2 = response2.json()
            print("Parsed JSON:", json.dumps(store_result2, indent=4))
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON Parse Error in Summarize Test: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())

