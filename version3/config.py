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

# -------- BRANDING --------
APP_NAME = "RAG Assistant"
APP_LOGO_TEXT = "R"  # Single letter/emoji for logo
# To use an image instead, set this path (relative to version3/):
# APP_LOGO_IMAGE = "assets/logo.png"
APP_LOGO_IMAGE = None

# -------- THEME COLORS --------
# Override these to customize the login page gradient
BRAND_PRIMARY = "#0a84ff"    # Apple blue
BRAND_SECONDARY = "#5856d6"  # Apple purple
BRAND_SUCCESS = "#30d158"    # Apple green

# NOTE: These settings match your working version2 setup.
# Docker and Ollama are already configured and running.
