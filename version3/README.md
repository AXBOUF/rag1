# Version 3: Privacy-Aware RAG System

A production-ready RAG system with **role-based access control**, **LLM-based content classification**, and **audit logging**.

## 🎯 Key Features

### 🔒 Privacy & Security
- **LLM-Based Classification**: Automatic content sensitivity analysis (PUBLIC/INTERNAL/CONFIDENTIAL)
- **Role-Based Access Control**: Three roles with different access levels
  - 👤 **Employee**: PUBLIC only
  - 👔 **Manager**: PUBLIC + INTERNAL
  - 👑 **Admin**: PUBLIC + INTERNAL + CONFIDENTIAL
- **Filtered Retrieval**: ChromaDB WHERE clauses prevent unauthorized access
- **Audit Logging**: Complete query trail for compliance

### 🎨 Clean Design
- **Dark Theme**: Minimal, professional UI (background: #1f1f23)
- **Color-Coded Badges**: Visual sensitivity indicators
- **Responsive Layout**: Works on desktop and mobile
- **Accessibility**: WCAG AA contrast ratios

### 🧠 Smart Classification
- Uses Ollama to analyze each text chunk
- Context-aware sensitivity detection
- Handles mixed-sensitivity documents
- Configurable classification rules

## 📁 Project Structure

```
version3/
├── app.py                      # Streamlit web UI
├── interactive_query.py        # CLI interface
├── ingest_with_privacy.py      # Document ingestion with classification
├── query_with_privacy.py       # Role-filtered query engine
├── demo.py                     # Side-by-side role comparison
├── theme/
│   ├── styles.py              # Dark theme CSS
│   └── constants.py           # Icons, colors, prompts
├── utils/
│   ├── classifier.py          # LLM-based classifier
│   ├── metadata.py            # Enhanced metadata schema
│   └── audit_log.py           # Audit logging system
├── test_data/                 # Test documents directory
│   ├── public/
│   ├── internal/
│   └── confidential/
└── .streamlit/
    └── config.toml            # Dark theme configuration
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Make sure ChromaDB is running
docker-compose up -d

# Ensure Ollama models are pulled
ollama pull qwen2.5:7b
ollama pull mxbai-embed-large:latest
```

### 2. Add Your Documents

Place PDFs in `version3/test_data/` (anywhere - classification is automatic)

```bash
cp your-documents/*.pdf version3/test_data/
```

### 3. Ingest Documents

```bash
python version3/ingest_with_privacy.py
```

This will:
- Process all PDFs in test_data/
- Classify each chunk using LLM
- Store with enhanced metadata in ChromaDB

**Expected Output:**
```
🧠 Privacy-Aware RAG Ingestion
ℹ️ Using LLM-based classification

📄 Ingesting: version3/test_data/document.pdf
   Pages: 5
   ⏳ Classifying page 1... 🟢 PUBLIC
   ⏳ Classifying page 2... 🟡 INTERNAL
   ⏳ Classifying page 3... 🔒 CONFIDENTIAL
   ...
   ✅ Stored 5 chunks
   🟢 PUBLIC: 2 | 🟡 INTERNAL: 2 | 🔒 CONFIDENTIAL: 1

🎉 Ingestion Complete!
```

### 4. Query the System

**Option A: Web UI (Recommended)**
```bash
streamlit run version3/app.py
```

Features:
- Role selector dropdown
- Chat interface
- Real-time classification badges
- Audit log viewer
- Retrieved context display

**Option B: CLI Interface**
```bash
python version3/interactive_query.py
```

Features:
- Interactive role selection
- Conversational queries
- Execution time display
- Filtering notifications

**Option C: Demo Comparison**
```bash
python version3/demo.py
```

Shows side-by-side results for different roles with the same query.

## 🎨 Design System

### Color Palette

| Use Case | Color | Hex |
|----------|-------|-----|
| Background | Near-black | #1f1f23 |
| Surface | Dark gray | #2d2d31 |
| Accent | Emerald | #10b981 |
| Public | Green | #10b981 |
| Internal | Amber | #f59e0b |
| Confidential | Red | #ef4444 |

### Icons

| Entity | Icon |
|--------|------|
| Employee | 👤 |
| Manager | 👔 |
| Admin | 👑 |
| Public | 🟢 |
| Internal | 🟡 |
| Confidential | 🔒 |

## 🔐 Security Features

### 1. Classification Rules

The LLM classifier uses these guidelines:

- **PUBLIC**: General information, no sensitive data
  - Product brochures, public documentation
  - Blog posts, marketing materials
  
- **INTERNAL**: Company-specific, not publicly available
  - Internal processes, employee handbooks
  - Standard operating procedures
  
- **CONFIDENTIAL**: Highly sensitive data
  - PII (personal identifiable information)
  - Financial data, salary information
  - Trade secrets, legal documents

### 2. Access Control Matrix

| Role | PUBLIC | INTERNAL | CONFIDENTIAL |
|------|--------|----------|--------------|
| Employee | ✅ | ❌ | ❌ |
| Manager | ✅ | ✅ | ❌ |
| Admin | ✅ | ✅ | ✅ |

### 3. Filtering Mechanism

**At Retrieval Time:**
```python
# ChromaDB WHERE filter example
where_filter = {"sensitivity_level": {"$in": ["public", "internal"]}}
results = collection.query(query_embedding, where=where_filter)
```

**Benefits:**
- Documents never leave the database if unauthorized
- No post-processing filtering (true privacy)
- Efficient (filtered at query time)

### 4. Prompt Hardening

The LLM is explicitly instructed:
```
ONLY answer based on the provided context.
DO NOT generate information outside retrieved documents.
If context doesn't contain the answer, say so clearly.
```

### 5. Audit Logging

Every query logs:
- Timestamp
- User role
- Query text
- Retrieved document IDs
- Sensitivity levels accessed
- Response preview
- Execution time
- Status (success/filtered/error)

**Log Location:** `version3/logs/audit_YYYYMMDD.jsonl`

## 📊 Example Use Cases

### Corporate Knowledge Base
- Employees: Access public documentation
- Managers: Also see internal processes
- Executives: Access financial reports

### Healthcare System
- Nurses: General medical info
- Doctors: Patient records (non-sensitive)
- Administrators: Full access including billing

### Legal Firm
- Paralegals: Public legal documents
- Associates: Client communications
- Partners: Privileged information

## 🧪 Testing

### Test Classification
```bash
cd version3/utils
python classifier.py
```

### Test Metadata
```bash
cd version3/utils
python metadata.py
```

### Test Audit Log
```bash
cd version3/utils
python audit_log.py
```

## 📈 Performance Considerations

### Classification Speed
- ~2-5 seconds per chunk (depends on LLM)
- Parallel processing possible (future enhancement)
- Classification happens once at ingestion

### Query Speed
- ~1-2 seconds per query
- Most time spent on LLM generation
- Retrieval is fast (<100ms)

### Optimization Tips
1. Use smaller LLM for classification (e.g., qwen2.5:3b)
2. Batch classify multiple chunks
3. Cache embeddings
4. Use GPU acceleration for Ollama

## 🔧 Configuration

### Environment Variables

Create `version3/.env`:
```
OLLAMA_BASE=http://localhost:11434
CHROMA_HOST=localhost
CHROMA_PORT=8000
API_KEY=your_secret_key
DEFAULT_MODEL=qwen2.5:7b
EMBED_MODEL=mxbai-embed-large:latest
```

### Custom Classification Rules

Edit `theme/constants.py`:
```python
CLASSIFICATION_PROMPT = """
Your custom classification instructions here...
"""
```

### Role Customization

Edit `theme/constants.py`:
```python
ROLE_ACCESS = {
    "employee": ["public"],
    "manager": ["public", "internal"],
    "admin": ["public", "internal", "confidential"],
    "auditor": ["public", "internal"],  # Add custom role
}
```

## 🐛 Troubleshooting

### ChromaDB Connection Error
```bash
# Check if ChromaDB is running
docker ps | grep chroma

# Restart if needed
docker-compose restart chromadb
```

### Classification Timeout
```python
# In utils/classifier.py, increase timeout:
classifier.classify_chunk(text, timeout=60)
```

### Ollama Connection Error
```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Check if models are pulled
ollama list
```

## 📝 Future Enhancements

- [ ] Document upload via web UI
- [ ] Real-time classification progress bar
- [ ] Export audit logs to CSV/PDF
- [ ] Multi-language support
- [ ] Batch query comparison UI
- [ ] Role hierarchy (inherited permissions)
- [ ] Time-based access (temporary elevation)
- [ ] Document expiration policies

## 🤝 Contributing

This is a demo/educational project. Feel free to extend it for your use case!

## 📄 License

Same as parent project.

---

**Built with:** Python, Streamlit, ChromaDB, Ollama, PyPDF  
**Design:** Clean minimal dark theme  
**Security:** Role-based access control + Audit logging
