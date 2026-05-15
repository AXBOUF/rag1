"""
Minimal config for EVALUATION environment.
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
COLLECTION_NAME = "evaluation_collection"

# -------- API AUTHENTICATION --------
API_KEY = "mysecretkey"
HEADERS = {"x-api-key": API_KEY}

# -------- DOCUMENT PROCESSING --------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# -------- TEST DATA --------
# Default test dir for evaluation (relative to workspace root)
TEST_DATA_DIR = "EVALUATION/test_data"

# -------- BRANDING --------
APP_NAME = "RAG Evaluation"
APP_LOGO_TEXT = "E"
APP_LOGO_IMAGE = None

# -------- THEME COLORS --------
BRAND_PRIMARY = "#0a84ff"
BRAND_SECONDARY = "#5856d6"
BRAND_SUCCESS = "#30d158"
