"""
Dual-model evaluation runner for the EVALUATION collection.

Flow:
- embed the user query with Ollama
- retrieve matching chunks from ChromaDB using role filtering
- generate one answer from Ollama
- generate one answer from Anthropic Haiku
- ask Anthropic Haiku to compare the two answers
"""
import anthropic
import argparse
import json
import os
import sys
from pathlib import Path

import requests
from chromadb import HttpClient

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass  # dotenv not available, use env vars directly

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from theme.constants import (
    API_KEY,
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    DEFAULT_MODEL,
    EMBED_MODEL,
    OLLAMA_BASE,
    QUERY_SYSTEM_PROMPT,
    ROLE_ACCESS,
    ROLE_ICONS,
    STATUS_ICONS,
)
from utils.metadata import format_metadata_display, get_chromadb_where_filter


HEADERS = {"x-api-key": API_KEY}
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
DEFAULT_EVAL_PROMPT = "What are the uniform rules?"


def get_embedding(text: str) -> list[float]:
    response = requests.post(
        f"{OLLAMA_BASE}/embed",
        json={"model": EMBED_MODEL, "text": text[:500]},
        headers=HEADERS,
        timeout=30,
    )
    if response.status_code != 200:
        raise Exception(f"Embedding API returned status {response.status_code}")
    return response.json()["embedding"]


def retrieve_context(collection, query: str, role: str, top_k: int = 3):
    role_lower = role.lower()
    if role_lower not in ROLE_ACCESS:
        raise ValueError(f"Invalid role: {role}. Must be one of {list(ROLE_ACCESS.keys())}")

    print(f"{STATUS_ICONS['progress']} Embedding query...")
    query_embedding = get_embedding(query)

    where_filter = get_chromadb_where_filter(role_lower)
    allowed_levels = ROLE_ACCESS[role_lower]

    print(f"{STATUS_ICONS['search']} Searching with role: {ROLE_ICONS[role_lower]} {role.upper()}")
    print(f"   Allowed levels: {', '.join(level.upper() for level in allowed_levels)}")

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []

    if not documents:
        return [], [], [], "I don't have access to documents that can answer this question with your current role."

    print(f"{STATUS_ICONS['success']} Retrieved {len(documents)} chunks")
    print(f"\n{STATUS_ICONS['info']} Retrieved Context:")
    for index, (doc, meta) in enumerate(zip(documents, metadatas), 1):
        print(f"   {index}. {format_metadata_display(meta)}")
        print(f"      Preview: {doc[:100]}...")

    context = "\n\n---\n\n".join(
        f"Document: {meta['filename']} (page {meta['page']}) [Sensitivity: {meta.get('sensitivity_level', 'unknown').upper()}]\n{doc}"
        for doc, meta in zip(documents, metadatas)
    )

    return documents, metadatas, distances, context


def ollama_answer(query: str, role: str, context: str) -> str:
    required_role = "Manager or Admin"
    if role.lower() == "manager":
        required_role = "Admin"

    system_prompt = QUERY_SYSTEM_PROMPT.format(
        context=context,
        role_upper=role.upper(),
        required_role=required_role,
    )

    try:
        response = requests.post(
            f"{OLLAMA_BASE}/llm",
            json={
                "model": DEFAULT_MODEL,
                "prompt": f"{system_prompt}\n\nUser Question: {query}\n\nAnswer:",
            },
            headers=HEADERS,
            timeout=120,
        )
        if response.status_code != 200:
            raise Exception(f"Ollama LLM API returned status {response.status_code}")
        return response.json()["response"]
    except requests.exceptions.Timeout:
        raise Exception(f"Ollama timeout at {OLLAMA_BASE}. Check if endpoint is reachable.")
    except requests.exceptions.ConnectionError as e:
        raise Exception(f"Cannot connect to Ollama at {OLLAMA_BASE}: {e}")


def anthropic_answer(query: str, role: str, context: str) -> str:
    if not ANTHROPIC_API_KEY:
        return None  # Skip if no API key

    prompt = (
        f"You are answering a role-restricted query for a {role.upper()} user. "
        f"Use only the context below. If the answer is not supported, say so.\n\n"
        f"Context:\n{context}\n\nQuestion:\n{query}"
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=800,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return response.content[0].text.strip()
    except anthropic.AuthenticationError:
        key_status = "set (length: {})".format(len(ANTHROPIC_API_KEY)) if ANTHROPIC_API_KEY else "NOT SET"
        print(f"⚠️  Anthropic authentication failed. ANTHROPIC_API_KEY is {key_status}")
        print(f"     Make sure your .env has: ANTHROPIC_API_KEY=sk-...")
        return None
    except anthropic.APIError as e:
        print(f"⚠️  Anthropic API error: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Unexpected error calling Anthropic: {e}")
        return None


def compare_with_anthropic(query: str, role: str, context: str, ollama_response: str, anthropic_response: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "ANTHROPIC_API_KEY is not set, so comparison was skipped."

    prompt = f"""You are comparing two assistant answers to the same role-restricted question.

Question:
{query}

Role:
{role.upper()}

Context:
{context}

Ollama answer:
{ollama_response}

Anthropic Haiku answer:
{anthropic_response}

Task:
- Decide which answer is better and why.
- Score each answer from 1 to 10 for factuality, usefulness, and access-control correctness.
- Mention if either answer leaks restricted information or ignores the role.
- End with a single recommendation: OLLAMA, ANTHROPIC, or TIE.
"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=800,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return response.content[0].text.strip()
    except Exception as e:
        raise Exception(f"Anthropic compare API error: {e}")


def load_prompts_from_markdown(prompt_file: str) -> list[str]:
    path = Path(prompt_file)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    prompts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            prompts.append(stripped[2:].strip())

    return prompts


def run_evaluation(query: str, role: str, top_k: int, as_json: bool = False) -> dict:
    print(f"{STATUS_ICONS['brain']} EVALUATION Model Comparison")
    print(f"Query: {query}")
    print(f"Role: {role.upper()}\n")

    chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    collection_count = collection.count()
    print(f"{STATUS_ICONS['success']} Connected to collection: {COLLECTION_NAME} ({collection_count} chunks)\n")

    if collection_count == 0:
        result = {
            "query": query,
            "role": role,
            "status": "empty_collection",
            "response": f"Collection {COLLECTION_NAME} is empty. Run EVALUATION/ingest_with_privacy.py first.",
        }
        print(result["response"])
        if as_json:
            print(json.dumps(result, indent=2))
        return result

    documents, metadatas, distances, context = retrieve_context(collection, query, role, top_k=top_k)
    if not documents:
        result = {
            "query": query,
            "role": role,
            "status": "no_results",
            "response": context,
        }
        print(context)
        if as_json:
            print(json.dumps(result, indent=2))
        return result

    print(f"\n{STATUS_ICONS['brain']} Generating Ollama answer...")
    try:
        ollama_response = ollama_answer(query, role, context)
    except Exception as e:
        ollama_response = f"Error: {e}"
    print("\n--- Ollama Answer ---")
    print(ollama_response)

    anthropic_response = None
    comparison = None
    if ANTHROPIC_API_KEY:
        print(f"\n{STATUS_ICONS['brain']} Generating Anthropic Haiku answer...")
        anthropic_response = anthropic_answer(query, role, context)
        if anthropic_response:
            print("\n--- Anthropic Haiku Answer ---")
            print(anthropic_response)

            print(f"\n{STATUS_ICONS['brain']} Comparing answers with Anthropic Haiku...")
            comparison = compare_with_anthropic(query, role, context, ollama_response, anthropic_response)
            print("\n--- Comparison ---")
            print(comparison)
    else:
        print(f"\n{STATUS_ICONS['info']} Skipping Anthropic (ANTHROPIC_API_KEY not set). Run with Ollama only.")

    result = {
        "query": query,
        "role": role,
        "status": "success",
        "retrieved_count": len(documents),
        "documents": documents,
        "metadatas": metadatas,
        "distances": distances,
        "ollama_response": ollama_response,
    }
    if anthropic_response:
        result["anthropic_response"] = anthropic_response
    if comparison:
        result["comparison"] = comparison

    if as_json:
        print("\n" + json.dumps(result, indent=2))

    return result


def main():
    parser = argparse.ArgumentParser(description="Compare Ollama and Anthropic Haiku answers against EVALUATION collection")
    parser.add_argument("query", nargs="?", help="User query to evaluate")
    parser.add_argument("--role", default=None, choices=list(ROLE_ACCESS.keys()), help="User role for retrieval filtering")
    parser.add_argument("--top-k", type=int, default=3, help="Number of chunks to retrieve")
    parser.add_argument("--prompt-file", type=str, help="Markdown file containing bullet prompts to run")
    parser.add_argument("--json", action="store_true", help="Print the final result as JSON")
    args = parser.parse_args()

    # Interactive prompts if not provided
    if not args.query and not args.prompt_file:
        print(f"{STATUS_ICONS['info']} Interactive Evaluation Mode\n")
        args.query = input("Enter your query: ").strip()
        if not args.query:
            args.query = DEFAULT_EVAL_PROMPT
            print(f"{STATUS_ICONS['warning']} Using default prompt: {args.query}")

    if not args.role:
        print(f"\n{STATUS_ICONS['info']} Available roles:")
        roles_list = list(ROLE_ACCESS.keys())
        for i, role in enumerate(roles_list, 1):
            print(f"  {i}. {role}")
        
        while True:
            role_input = input(f"\nSelect role (1-{len(roles_list)}) [default: employee]: ").strip()
            if not role_input:
                args.role = "employee"
                break
            try:
                idx = int(role_input) - 1
                if 0 <= idx < len(roles_list):
                    args.role = roles_list[idx]
                    break
                else:
                    print(f"{STATUS_ICONS['error']} Invalid selection. Please enter 1-{len(roles_list)}")
            except ValueError:
                print(f"{STATUS_ICONS['error']} Invalid input. Please enter a number.")
    else:
        args.role = args.role or "employee"

    prompts = []
    if args.prompt_file:
        prompts = load_prompts_from_markdown(args.prompt_file)
        if not prompts:
            raise ValueError(f"No bullet prompts found in {args.prompt_file}")
    elif args.query:
        prompts = [args.query]
    else:
        prompts = [DEFAULT_EVAL_PROMPT]
        print(f"{STATUS_ICONS['warning']} Using default prompt: {DEFAULT_EVAL_PROMPT}")

    if len(prompts) > 1:
        print(f"{STATUS_ICONS['info']} Running batch evaluation for {len(prompts)} prompts\n")

    all_results = []
    batch_mode = len(prompts) > 1
    for prompt in prompts:
        result = run_evaluation(prompt, args.role, args.top_k, as_json=args.json and not batch_mode)
        all_results.append(result)
        if batch_mode:
            print("\n" + "=" * 80 + "\n")

    if batch_mode and args.json:
        print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()