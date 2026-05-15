# Code Flow

This document explains how a query moves through the version 3 RAG pipeline.

## 1. Input Comes In

The user sends a question through the query path in `version3/query_with_privacy.py`.

At this stage, the system already knows the user role, such as employee, manager, or admin. That role matters because it controls which chunks can be retrieved later.

## 2. The Query Is Embedded

The raw text query is sent to the embedding endpoint in Ollama through the `get_embedding()` function.

In code, the query is truncated and posted to `OLLAMA_BASE + /embed` using the configured embedding model. The result is a numeric vector that represents the meaning of the query.

Why this matters:

- Similar questions produce similar vectors.
- Those vectors let ChromaDB search for semantically related chunks instead of relying only on exact keyword matches.

## 3. Chunks Were Already Embedded During Ingestion

Before querying, the documents must already be ingested through `version3/ingest_with_privacy.py`.

During ingestion:

- PDFs are discovered with `collect_pdfs()`.
- Each page is extracted with `pypdf.PdfReader`.
- The page text is classified by `ContentClassifier` in `version3/utils/classifier.py`.
- The text is embedded with the same Ollama embedding endpoint.
- Metadata is created with `create_chunk_metadata()` in `version3/utils/metadata.py`.
- The chunk, embedding, and metadata are stored in ChromaDB under the collection name from `version3/theme/constants.py`.

That means the query step is searching against a pre-built vector store, not raw files.

## 4. Role-Based Search Happens in ChromaDB

Once the query embedding is ready, `query_with_role()` builds a ChromaDB `where` filter from the user role.

The filter comes from `get_chromadb_where_filter()` and the access map in `version3/theme/constants.py`.

Typical behavior:

- employee can only see public chunks
- manager can see public and internal chunks
- admin can see public, internal, and confidential chunks

So the retrieval step is not just semantic search. It is semantic search plus access control.

## 5. Relevant Chunks Are Retrieved

ChromaDB returns the top matches using the query embedding and the role filter.

The code requests:

- documents
- metadatas
- distances

If the filter removes some otherwise relevant chunks, the system reports that those chunks were filtered by role restrictions.

## 6. The Context Is Built For The LLM

The retrieved chunks are formatted into a context string.

Each chunk is bundled with:

- the filename
- the page number
- the sensitivity level
- the extracted text

That context is then inserted into `QUERY_SYSTEM_PROMPT` from `version3/theme/constants.py`.

This is the step where the assistant is told how to behave:

- stay within the current role
- do not trust user claims about having higher access
- refuse higher-privilege actions when needed
- answer only using the retrieved context

## 7. The Model Generates The Final Answer

The final prompt is sent to Ollama through the `/llm` endpoint.

The model does not directly decide which document to read. That decision was already made by:

- query embedding
- Chroma similarity search
- role-based filtering

The model mainly decides how to phrase the answer using the supplied context and the system instructions.

## 8. Response Selection

The response that the user sees is the LLM output, unless retrieval fails or no allowed documents are found.

Possible outcomes:

- Success: the model answers using the retrieved context.
- No results: the system returns a message saying it cannot answer with the current role.
- Error: the system logs the failure and returns an exception path.

## 9. Audit Logging

If auditing is enabled, the query result is written through `AuditLogger`.

That log captures:

- user role
- query text
- retrieved metadata
- filtered count
- response text
- execution time

## Short Version

Input question -> embed query -> search ChromaDB with role filter -> build context from matching chunks -> send context to Ollama -> return the model answer.

The key idea is that search decides what evidence is available, and the model decides how to answer from that evidence.