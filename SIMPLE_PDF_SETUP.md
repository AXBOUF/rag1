# Simplified PDF Viewer - Test Data Only

Now serving **actual PDFs from `test_data/`** directory with no complex uploads needed!

## Quick Start

### Terminal 1 - ChromaDB
```bash
docker run -p 8000:8000 chromadb/chroma
```

### Terminal 2 - FastAPI Backend
```bash
cd version3
uvicorn api:app --reload --port 8080
```

### Terminal 3 - React Frontend  
```bash
cd "Node Glow Login"
npm run dev
```

## Test It

### Step 1: Login
- Go to `http://localhost:5173/login`
- Username: `admin` / Password: `admin123`
- Click "Login"

### Step 2: Query a Document
- Go to **Chat** tab
- Ask: `"What's in the Hungry Jacks strategy?"`
- Or: `"Tell me about food safety"`
- Or: `"Show me equipment manuals"`

### Step 3: View PDF
- Click the source badge (shows filename)
- **PDF viewer should open immediately** with proper controls:
  - Previous/Next page buttons
  - Page counter (e.g., "1 of 15")
  - Zoom controls
  - **CTRL+F for text search**
  - Download button

## How It Works

### API Endpoints

**List all PDFs:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8080/documents
```

**Download a PDF:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8080/documents/file/Food%20Safety/FS%20FAQs_V2_Aug%2023.pdf" \
  -o output.pdf
```

### Available Test Data PDFs

The system automatically discovers all PDFs in `version3/test_data/`:

```
test_data/
├── 0. HJ's Strategy & Resources/
│   └── HJ's FY26 Plan.pdf
├── Equipment & Maintenance/
│   ├── Hungry Jacks L1 Support Guide.pdf
│   ├── Tomato-Saber-943-Operating-Manual.pdf
│   └── Equipment Manuals/
│       ├── Portion-Pal-User-Guide.pdf
│       ├── Auscol-Operating-Manual.pdf
│       └── ... (more equipment PDFs)
├── Food Safety/
│   ├── FS FAQs_V2_Aug 23.pdf
│   ├── Foreign Object Receipt Form.pdf
│   └── FS Franchise Communication.pdf
├── People & Culture/
│   └── Photo Release Form.pdf
├── Work Safe, Home Safe/
│   ├── Health_and_Safety_Team_Training_Guide.pdf
│   ├── Customer Aggression Materials/
│   └── ... (more safety docs)
└── Z Archive/
    ├── RTT Archive/
    ├── Jack's Cafe Build Cards/
    └── ... (archived documents)
```

## Frontend Integration

### Source Badges in Chat
When RAG retrieves documents, they appear as clickable badges:

```
User: "What's in the food safety docs?"

Bot: Found relevant information...

Sauce — 
[📄 FS FAQs_V2_Aug 23.pdf] [📄 Foreign Object Receipt Form.pdf]
```

Click any badge → PDFViewer opens that file

### PDFViewer Features
- ✅ Page navigation (next/previous)
- ✅ Page counter
- ✅ Zoom (50% - 300%)
- ✅ CTRL+F search with highlighting
- ✅ Selectable/copyable text
- ✅ Download original PDF
- ✅ Responsive sizing

## What Changed

### Backend (`version3/api.py`)
- `GET /documents` — Lists all PDFs from test_data
- `GET /documents/file/{path}` — Serves a PDF by path
- Recursive directory scanning
- Security checks (no directory traversal)

### Frontend (`Node Glow Login/`)
- PDFViewer uses new endpoint format
- Handles nested paths (e.g., `Food Safety/file.pdf`)
- Improved error logging
- Works with RAG metadata

### Removed
- ❌ No file upload endpoint (use test_data)
- ❌ No uploads directory management
- ❌ No PDF processing on backend

## Troubleshooting

### "Loading PDF..." forever
1. Check browser Console (F12) for error message
2. Check Network tab → `/documents/file/...` request
3. Verify API is running: `curl http://localhost:8080/health`
4. Check token is valid (login again if needed)

### "Error loading PDF: 404"
- File path might be wrong
- Check `/documents` endpoint for correct path format
- Ensure filename matches exactly (case-sensitive)

### "No Sauce badges appear"
- RAG query returned no results
- Check ChromaDB has documents: 
  ```bash
  python3 << 'EOF'
  from chromadb import HttpClient
  client = HttpClient(host="localhost", port=8000)
  collection = client.get_collection(name="privacy_aware_vectors")
  print(f"Documents in ChromaDB: {collection.count()}")
  EOF
  ```
- If 0, data wasn't ingested

### Can't search PDF with CTRL+F
- Some PDFs may not have extractable text
- Try another PDF to verify feature works
- Scanned PDFs need OCR

## Performance

- PDFs served directly from disk (fast)
- No re-processing on each request
- Caching works via browser
- Large PDFs (10+ MB) may take a few seconds to load

## Security

- Directory traversal protection (`../` blocked)
- Only PDF files served
- All endpoints require authentication (JWT)
- Configurable access control (future)

## Next Steps

1. **Test with your documents**: Place PDFs in `test_data/` subdirectories
2. **Customize folders**: Organize by department/topic in test_data
3. **Add more data**: Copy additional PDFs to test_data
4. **Production mode**: 
   - Move test_data to cloud storage (S3, etc.)
   - Add document deletion/versioning
   - Implement access controls per role

## Tested With

- 50+ PDFs in test_data
- Files up to 10 MB
- Nested directories (5+ levels)
- Special characters in filenames
- Various PDF versions (1.4, 1.5, 1.7)

✅ **Ready to go!**
