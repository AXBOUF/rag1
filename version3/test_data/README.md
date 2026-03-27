# Test Data Directory

This directory is structured for testing the privacy-aware RAG system with role-based access control.

## Structure

```
test_data/
├── public/          → Documents classified as PUBLIC
├── internal/        → Documents classified as INTERNAL
└── confidential/    → Documents classified as CONFIDENTIAL
```

## How It Works

Documents placed in these folders will be used for **manual testing** (folder-based classification) or as reference material. However, the main ingestion system uses **LLM-based classification** which automatically analyzes each chunk's content and assigns sensitivity levels regardless of folder location.

## Usage

### For Testing with Pre-Classified Documents:
Place your PDFs in the appropriate folders:

- **public/** - General information, marketing materials, public documentation
- **internal/** - Internal processes, employee handbooks, operational guides
- **confidential/** - Financial reports, PII, trade secrets, executive communications

### For Automatic Classification:
You can place all PDFs in a single folder and let the LLM classifier analyze each chunk independently.

## Classification Examples

### 🟢 PUBLIC
- Product brochures
- Public blog posts
- General company information
- Open-source documentation

### 🟡 INTERNAL
- Employee onboarding guides
- Internal wikis
- Standard operating procedures
- Team meeting notes (non-sensitive)

### 🔒 CONFIDENTIAL
- Financial statements
- Employee personal records
- Salary information
- Legal contracts
- Strategic plans
- Customer PII

## Role Access Matrix

| Role     | Can Access                           | Icon |
|----------|--------------------------------------|------|
| Employee | 🟢 PUBLIC only                       | 👤   |
| Manager  | 🟢 PUBLIC + 🟡 INTERNAL              | 👔   |
| Admin    | 🟢 PUBLIC + 🟡 INTERNAL + 🔒 CONFIDENTIAL | 👑   |

## Next Steps

1. Add your test PDFs to these folders
2. Run the ingestion script: `python version3/ingest_with_privacy.py`
3. Query the system with different roles: `python version3/interactive_query.py`
4. View results in the web UI: `streamlit run version3/app.py`
