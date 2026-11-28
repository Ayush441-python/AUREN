import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AUREN Risk API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://aurenfrontend-delta.vercel.app",
        "https://aurenfrontend-five.vercel.app",
        "https://auren-api-8yrq.onrender.com",
        "http://localhost:3000",
        "http://localhost:5500",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]
    CORS_ORIGIN_REGEX: str = r"^https://.*\.vercel\.app$"

    # LLM Settings
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

    # Web3 / Base RPC
    BASE_RPC_URL: str = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")


settings = Settings()
