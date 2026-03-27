"""
Configuration file for version3 privacy-aware RAG.
All settings from working version2 setup.
"""

# -------- OLLAMA CONFIGURATION --------
OLLAMA_BASE = "http://www.munalbaraili.com"
DEFAULT_MODEL = "qwen2.5:7b"
EMBED_MODEL = "mxbai-embed-large:latest"

# -------- API ENDPOINTS --------
EMBED_ENDPOINT = f"{OLLAMA_BASE}/api/embed"
LLM_ENDPOINT = f"{OLLAMA_BASE}/api/llm"
GENERATE_ENDPOINT = f"{OLLAMA_BASE}/api/generate"

# -------- CHROMADB CONFIGURATION --------
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
COLLECTION_NAME = "privacy_aware_vectors"

# -------- API AUTHENTICATION --------
API_KEY = "mysecretkey"
HEADERS = {"x-api-key": API_KEY}

# -------- DOCUMENT PROCESSING --------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# -------- TEST DATA --------
TEST_DATA_DIR = "version3/test_data"

# NOTE: These settings match your working version2 setup.
# Docker and Ollama are already configured and running.
