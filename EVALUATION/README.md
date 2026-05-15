EVALUATION - Minimal evaluation copy of version3

- Collection name: `evaluation_collection` (set in `config.py`).
- Default test data dir: `EVALUATION/test_data`

How to run (from workspace root):

1. Activate your Python venv:

```bash
source /home/mun/ragt1/venv/bin/activate
```

2. (Optional) Install dependencies into the venv:

```bash
pip install -r EVALUATION/requirements.txt
```

3. Run ingestion (CSV files are ignored; add PDFs into `EVALUATION/test_data`):

```bash
python EVALUATION/ingest_with_privacy.py --dir EVALUATION/test_data
```

4. Compare an answer from Ollama and Anthropic Haiku against the same retrieved context:

```bash
export ANTHROPIC_API_KEY="your-key-here"
python EVALUATION/compare_responses.py "What are the uniform rules?" --role employee
```

5. Run the whole prompt list from `prompt_test.md`:

```bash
export ANTHROPIC_API_KEY="your-key-here"
python EVALUATION/compare_responses.py --prompt-file EVALUATION/prompt_test.md --role employee
```

Notes:
- This is a minimal copy intended for quick evaluation. Ollama and ChromaDB should be accessible as in your original setup.
- The ingestion script will connect to the ChromaDB instance at `localhost:8000` and use collection `evaluation_collection`.
- If you omit the query, the runner falls back to a safe default prompt.
- The comparison script calls Ollama for the main answer, Anthropic Haiku for a second answer, and Anthropic again to compare both responses.
