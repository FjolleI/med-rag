"""Pytest config: force mock mode so tests never touch real Pinecone/OpenAI."""

import os

os.environ["PINECONE_API_KEY"] = "mock-dev"
os.environ["OPENAI_API_KEY"] = "mock-dev"
os.environ["ANTHROPIC_API_KEY"] = "mock-dev"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["ENVIRONMENT"] = "test"
