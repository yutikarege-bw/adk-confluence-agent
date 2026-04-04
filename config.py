import os
from dataclasses import dataclass
from dotenv import load_dotenv

import google.auth
from google.genai import types
from google.adk.models.google_llm import Gemini

load_dotenv()

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 502, 503, 504],
)

@dataclass
class Config:
    worker_model = Gemini(
        model="gemini-2.5-flash",
        retry_config=retry_config,
    )
    max_search_iterations: int = 5

config = Config()