
import os
from agent_prompts import prompts
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv
load_dotenv(override=True)

SYSTEM_PROMPT = prompts["SYSTEM_PROMPT"]
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
