# RAG1 — Retrieval-Augmented Generation with Ollama & ChromaDB

A local RAG (Retrieval-Augmented Generation) system that lets you chat with your PDF documents using locally-hosted LLMs via [Ollama](https://ollama.com) and a [ChromaDB](https://www.trychroma.com) vector database. An interactive [Streamlit](https://streamlit.io) web interface is included for conversational queries.

---

## Features

- **Local-first** — all inference runs through Ollama; no data leaves your machine
- **PDF ingestion** — index a single PDF or an entire directory of PDFs into ChromaDB
- **Semantic search** — queries are embedded and matched against stored document chunks
- **Streamlit chat UI** — real-time streaming responses, model selector, and temperature control
- **CLI tools** — inspect the vector store and test context retrieval from the terminal
- **Docker Compose** — one-command ChromaDB setup

---

## Architecture

```
User Query
    │
    ▼
Streamlit UI  ──────────────────────────────────────┐
    │                                                │
    ▼                                                │
1. Embed query   →  Ollama Embeddings API            │
    │                                                │
    ▼                                                │
2. Similarity search  →  ChromaDB                   │
    │                                                │
    ▼                                                │
3. Retrieve top-k document chunks                   │
    │                                                │
    ▼                                                │
4. Build prompt  (context + question)               │
    │                                                │
    ▼                                                │
5. Generate answer  →  Ollama LLM API               │
    │                                                │
    ▼                                                │
Display streamed response  ◄────────────────────────┘
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.8+ | Tested on 3.14.3 |
| [Ollama](https://ollama.com/download) | Must be running and accessible |
| Docker & Docker Compose | For the ChromaDB container |

### Required Ollama models

Pull these before running the project:

```bash
ollama pull qwen2.5:7b
ollama pull mxbai-embed-large
```

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/AXBOUF/rag1.git
cd rag1

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install streamlit requests chromadb pypdf ollama

# 4. Start ChromaDB
docker-compose up -d
```

---

## Configuration

Several values are currently hardcoded in the scripts. Update them to match your environment:

| Setting | Default | Files to update |
|---|---|---|
| Ollama host | `http://192.168.1.186:11434` | All scripts |
| Chat model | `qwen2.5:7b` | `chat.py`, `version1/ask.py`, `version2/ask_v2.py` |
| Embedding model | `mxbai-embed-large:latest` | `version1/pdf_to_chroma.py`, `version2/dir_to_chroma.py`, `context_view/context_finder.py` |
| ChromaDB host | `localhost` | All scripts |
| ChromaDB port | `8000` | All scripts |
| Collection name | `pdf_vectors` | All scripts |

---

## Usage

### 1. Verify Ollama connectivity

```bash
python handshake/handshake.py
```

### 2. Ingest documents

**Single PDF (Version 1):**

Place your PDF at `version1/scholarship.pdf`, then run:

```bash
python version1/pdf_to_chroma.py
```

**Directory of PDFs (Version 2 — recommended):**

Place your PDFs inside `./test1/`, then run:

```bash
python version2/dir_to_chroma.py
```

This recursively processes all PDFs in the directory and stores each page as a separate, metadata-tagged chunk.

### 3. Query via CLI

```bash
# Version 1
python version1/ask.py

# Version 2
python version2/ask_v2.py
```

Type your question at the prompt. The script retrieves the most relevant document chunks and generates a grounded answer.

### 4. Launch the chat UI

```bash
streamlit run chat.py
```

Open `http://localhost:8501` in your browser.

- **Model selector** — choose any model available in your Ollama instance
- **Temperature slider** — control response creativity (0.0 – 2.0)
- **Clear history** — reset the conversation

### 5. Inspect the vector store

```bash
# View all indexed chunks with metadata and embedding previews
python context_view/chroma.py

# Interactive context retrieval (returns top-k chunks for a query)
python context_view/context_finder.py
```

---

## Project Structure

```
rag1/
├── chat.py                        # Streamlit chat interface
├── docker-compose.yaml            # ChromaDB Docker service
├── context_view/
│   ├── chroma.py                  # Inspect all ChromaDB documents
│   └── context_finder.py          # CLI context retrieval tool
├── handshake/
│   ├── handshake.py               # Basic Ollama connectivity test
│   └── handshake.ipynb            # Jupyter notebook version
├── version1/
│   ├── pdf_to_chroma.py           # Ingest a single PDF into ChromaDB
│   └── ask.py                     # QA pipeline using top-3 context chunks
└── version2/
    ├── dir_to_chroma.py           # Batch-ingest a directory of PDFs
    └── ask_v2.py                  # QA pipeline (directory-based)
```

---

## License

This project is released for personal and educational use. See [LICENSE](LICENSE) for details.
