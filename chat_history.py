import os
import json
import logging
import re
import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from openai.types.create_embedding_response import CreateEmbeddingResponse
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncAzureOpenAI, AzureOpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from hashlib import sha256
from sentence_transformers import SentenceTransformer
import torch
from functools import cache, lru_cache
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable symlinks warning
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Model configuration
MODEL_NAME = "dunzhang/stella_en_400M_v5"
MODEL_PATH = "models/stella_en_400M_v5"
MODEL_REVISION = "main"  # Pin to specific version

class EmbeddingModel:
    _instance = None
    
    @classmethod
    def get_instance(cls) -> SentenceTransformer:
        if cls._instance is None:
            # Verify CUDA
            logger.info(f"CUDA available: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")

            # Initialize model with proper parameters
            cls._instance = SentenceTransformer(
                model_name_or_path=MODEL_NAME,
                device=device,
                cache_folder=MODEL_PATH,
                trust_remote_code=True,
                revision=MODEL_REVISION,
                local_files_only=False,  # Set to True after initial download
                config_kwargs={"use_memory_efficient_attention": False, "unpad_inputs": False}
            )
            logger.info("Initialized SentenceTransformer model")
        return cls._instance

# Get singleton model instance
embedding_model = EmbeddingModel.get_instance()

# Create necessary directories
SESSIONS_DIR = Path("logs/sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI setup
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2024-02-01"
os.environ["OPENAI_API_BASE"] = "https://centriaopenaidev.openai.azure.com/"
os.environ["OPENAI_API_KEY"] = "c1b675b6e1344180a583cfaa4d1b1b7d"  # Replace with secure value or env var

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

#Read requirements.txt and summarize the packages
with open('requirements.txt', 'r') as file:
    requirements = file.read()

SYSTEM_PROMPT = """
You are a helpful assistant that summarizes messages from users and their responses.
You will be given a list of messages from users and their responses.
You will need to summarize the messages and responses into a single context summary.

Python packages:
{requirements}
"""

from pydantic_ai import Agent

superAgent = Agent(
    model=openai_model,
    name="SuperAgent",
    system_prompt=SYSTEM_PROMPT,
    result_type=str,
    retries=3,
    model_settings={"temperature": 0.0}
)

# Pydantic models for request/response validation
class StoreRequest(BaseModel):
    user_email: EmailStr
    question: str
    category: str
    answer: str

class RetrieveRequest(BaseModel):
    user_email: EmailStr
    question: str
    k: Optional[int] = 5

class QAItem(BaseModel):
    question: str
    category: str
    answer: str
    similarity: Optional[float] = None
    timestamp: str

class RetrieveResponse(BaseModel):
    session_id: str
    session_exists: bool
    results: List[QAItem]
    count: int

class SummarizeResponse(BaseModel):
    session_id: str
    session_exists: bool
    top_relevant: List[QAItem]
    summary: str
    enhanced_question: str
    count: int

app = FastAPI()

async def get_embedding(text: str) -> List[float]:
    """Get embeddings using SentenceTransformer."""
    logger.info(f"Getting embedding for: {text}")
    # Use s2s_query prompt for sentence-to-sentence matching
    embedding = embedding_model.encode([text], prompt_name="s2s_query")[0]
    return embedding.tolist()

@lru_cache(maxsize=1000)
def calculate_cosine_similarity(embedding1: tuple[float, ...], embedding2: tuple[float, ...]) -> float:
    """Calculate cosine similarity between two embeddings."""
    logger.info("Calculating cosine similarity")
    emb1 = np.array(embedding1).reshape(1, -1)
    emb2 = np.array(embedding2).reshape(1, -1)
    return float(cosine_similarity(emb1, emb2)[0][0])

@cache
def get_session_path(session_id: str) -> Path:
    """Get the path for a session file."""
    return SESSIONS_DIR / f"qa_session_{session_id}.json"

@cache
def session_exists(session_id: str) -> bool:
    """Check if a session file exists."""
    return get_session_path(session_id).exists()

# Cache for QA data with TTL
_qa_cache = {}
_qa_cache_ttl = 60  # 60 seconds TTL

def read_qa_data(session_id: str) -> List[dict]:
    """Read QA data from session file with caching."""
    current_time = time.time()
    
    # Check cache
    if session_id in _qa_cache:
        data, timestamp = _qa_cache[session_id]
        if current_time - timestamp < _qa_cache_ttl:
            return data
    
    # Cache miss or expired, read from disk
    path = get_session_path(session_id)
    if not path.exists():
        data = []
    else:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            data = []
    
    # Update cache
    _qa_cache[session_id] = (data, current_time)
    return data

def write_qa_data(data: List[dict], session_id: str):
    """Write QA data to session file and update cache."""
    path = get_session_path(session_id)
    path.write_text(json.dumps(data, indent=2))
    # Update cache
    _qa_cache[session_id] = (data, time.time())

async def store_qa(question: str, category: str, answer: str, session_id: str):
    """Store a new Q&A entry."""
    logger.info(f"Storing QA for session: {session_id}")
    data = read_qa_data(session_id)
    question_embedding = await get_embedding(question)
    
    entry = {
        "question": question,
        "category": category,
        "answer": answer,
        "question_embedding": question_embedding,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    data.append(entry)
    write_qa_data(data, session_id)

async def retrieve_relevant_messages(question: str, session_id: str, k: int = 5) -> List[dict]:
    """Retrieve top-k relevant messages."""
    logger.info(f"Retrieving relevant messages for session: {session_id}")
    data = read_qa_data(session_id)
    if not data:
        return []

    # Filter duplicates keeping newest
    unique_questions = {}
    for item in data:
        question_text = item["question"]
        timestamp = item["timestamp"]
        if question_text not in unique_questions or unique_questions[question_text]["timestamp"] < timestamp:
            unique_questions[question_text] = item

    filtered_data = list(unique_questions.values())
    query_emb = await get_embedding(question)

    # Convert embeddings to tuples for caching
    query_emb_tuple = tuple(query_emb)
    
    for item in filtered_data:
        item_emb_tuple = tuple(item["question_embedding"])
        item["similarity"] = calculate_cosine_similarity(
            query_emb_tuple,
            item_emb_tuple
        )

    return sorted(filtered_data, key=lambda x: x["similarity"], reverse=True)[:k]

def clean_result_for_output(item: dict) -> dict:
    """Remove embedding data from result items."""
    cleaned = item.copy()
    cleaned.pop('question_embedding', None)
    return cleaned

@app.post("/store", response_model=dict)
async def store_endpoint(request: StoreRequest):
    """Store a new Q&A pair."""
    session_id = sha256(request.user_email.encode()).hexdigest()
    await store_qa(
        question=request.question,
        category=request.category,
        answer=request.answer,
        session_id=session_id
    )
    return {
        "message": f"Stored Q&A for question: '{request.question}'",
        "session_id": session_id,
        "session_exists": session_exists(session_id)
    }

@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_endpoint(request: RetrieveRequest):
    """Retrieve relevant Q&A pairs."""
    k = request.k if request.k is not None else 5
    if k < 1:
        raise HTTPException(status_code=400, detail="Parameter 'k' must be greater than 0")
    
    session_id = sha256(request.user_email.encode()).hexdigest()
    exists = session_exists(session_id)
    
    if not exists:
        return RetrieveResponse(
            session_id=session_id,
            session_exists=False,
            results=[],
            count=0
        )
    
    top_relevant = await retrieve_relevant_messages(
        question=request.question,
        session_id=session_id,
        k=k
    )
    
    cleaned_results = [QAItem(**clean_result_for_output(item)) for item in top_relevant]
    return RetrieveResponse(
        session_id=session_id,
        session_exists=True,
        results=cleaned_results,
        count=len(cleaned_results)
    )

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_endpoint(request: RetrieveRequest):
    """Retrieve and summarize relevant Q&A pairs."""
    k = request.k if request.k is not None else 5
    if not (1 <= k <= 25):
        raise HTTPException(
            status_code=400,
            detail="Parameter 'k' must be between 1 and 25"
        )
    
    session_id = sha256(request.user_email.encode()).hexdigest()
    exists = session_exists(session_id)
    
    if not exists:
        return SummarizeResponse(
            session_id=session_id,
            session_exists=False,
            top_relevant=[],
            summary="",
            enhanced_question="",
            count=0
        )
    
    top_relevant = await retrieve_relevant_messages(
        question=request.question,
        session_id=session_id,
        k=k
    )
    
    if not top_relevant:
        return SummarizeResponse(
            session_id=session_id,
            session_exists=True,
            top_relevant=[],
            summary="",
            enhanced_question="",
            count=0
        )
    
    logger.info(f"Summarizing top {k} chat history in relation to question '{request.question}'")
    message_prompt = (
        f"Please summarize the following top {k} chat history in relation to question '{request.question}':\n\n"
        f"{json.dumps([clean_result_for_output(item) for item in top_relevant], indent=2)}"
    )
    
    response = await superAgent.run(user_prompt=message_prompt)
    summary = response.data
    
    enhanced_query_prompt = f"""
    You are advising a coding agent interacting with a software engineer.
    You are given either an error message or a user question.
    You will also get to read the recent chat and error history.
    You are to enhance the question to be more specific and relevant to the chat history.
    If its an error message, recommend a solution given the chat history.

    Summary of chat history:
        '{summary}'

    If question, enhance it, if error message, recommend a solution given the chat history.
        '{request.question}' 

    
    #Do not comment or discuss. Simply return a more enhanced question in a way
    the coding agent will understand.
    """

    new_question_response = await superAgent.run(user_prompt=enhanced_query_prompt)
    new_question = new_question_response.data
    
    cleaned_relevant = [QAItem(**clean_result_for_output(item)) for item in top_relevant]
    return SummarizeResponse(
        session_id=session_id,
        session_exists=True,
        top_relevant=cleaned_relevant,
        summary=summary,
        enhanced_question=new_question,
        count=len(top_relevant)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("chat_history:app", host="0.0.0.0", port=8000, reload=True)
    print("Server is running on http://0.0.0.0:8000")
