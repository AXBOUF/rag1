# PDF Viewer Troubleshooting Guide

## Checklist

### 1. **Verify API is Running**
```bash
curl http://localhost:8080/health
# Should return: {"status":"ok"}
```

### 2. **Check PDF Upload Endpoint**
```bash
# First, get a token
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Response: {"access_token":"...", "user": {...}}
# Copy the access_token

# Then test upload
curl -X POST http://localhost:8080/admin/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "files=@/path/to/your/file.pdf"

# Should return:
# {"status":"success","message":"...","chunks_by_level":{...}}
```

### 3. **Check if PDFs are Saved**
```bash
ls -la version3/uploads/
# Should show uploaded PDF files

# If empty, upload failed
```

### 4. **Test PDF Download Endpoint**
```bash
curl http://localhost:8080/api/documents/your-file.pdf \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o downloaded.pdf

# If successful, you'll get a PDF file
# If 404, file wasn't saved during upload
# If 401, token is invalid/expired
```

### 5. **Check Browser Console**
When you click a source badge:

**Open Developer Tools (F12):**
- Go to **Console** tab
- Look for debug messages:
  - `🔍 PDFViewer mounted with filename: ...`
  - `📄 Attempting to load from: /api/documents/...`
  - `✅ PDF loaded successfully` or `❌ PDF Load Error: ...`

- Go to **Network** tab
- Click a source badge
- Look for requests to `/api/documents/filename.pdf`
- Check response status (should be 200)

### 6. **Verify ChromaDB Connection**
```bash
curl http://localhost:8000/api/v1/collections
# Should return a list of collections
```

### 7. **Check JWT Token Validity**
If getting "401 Unauthorized":
```bash
# Token may have expired
# Login again to get a fresh token
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## Common Issues & Fixes

### **Issue: "Loading PDF..." stays forever**

**Cause 1: PDF file doesn't exist**
```bash
# Check uploads directory
ls -la version3/uploads/
```
**Fix:** Re-upload the PDF

**Cause 2: API endpoint not responding**
```bash
# Check if API is running
curl http://localhost:8080/health
```
**Fix:** Start API: `cd version3 && uvicorn api:app --reload --port 8080`

**Cause 3: CORS issue**
- Check browser console for CORS error
- Verify `vite.config.ts` has proxy configured
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8080',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

### **Issue: "Error loading PDF: ..."**

**Check what the error says:**
- "Failed to fetch" → Network/CORS issue
- "404" → File not found in uploads/
- "Unexpected end of file" → PDF is corrupted

**Debug:**
```javascript
// In browser console, test the fetch
fetch('/api/documents/your-file.pdf', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
}).then(r => {
  console.log('Status:', r.status);
  console.log('Headers:', r.headers);
  return r.blob();
}).then(blob => {
  console.log('Blob size:', blob.size);
}).catch(e => console.error('Error:', e));
```

### **Issue: Source badge doesn't appear**

**Check API response:**
```javascript
// In browser console, log the last query response
// Open Network tab → click "Chat" query → find request to /api/query
// Check the response → look for "metadatas" array
```

**If metadatas are empty:**
- ChromaDB may have no documents
- Query returned no results
- Role access filtering blocked all results

**Check ChromaDB:**
```bash
python3 << 'EOF'
from chromadb import HttpClient
client = HttpClient(host="localhost", port=8000)
collection = client.get_collection(name="privacy_aware_vectors")
print(f"Total documents: {collection.count()}")
EOF
```

### **Issue: Upload says success but PDFs don't appear**

**Check upload response:**
```bash
# Look at the response message for details
# Should say "Processed X files, Y chunks"
```

**Check for errors in API logs:**
```bash
# Look at the terminal running uvicorn
# Check for exceptions or error messages
```

**Possible causes:**
1. PDF is corrupted
2. Ollama/embeddings API is not reachable
3. ChromaDB is down
4. No permissions on uploads directory

### **Issue: Can't find documents with CTRL+F**

**Cause:** PDF.js text extraction may have failed
- Scanned PDFs without OCR won't have searchable text
- Some corrupted PDFs don't have embedded text

**Fix:** Use the RAG search instead (query in chat)

---

## Step-by-Step Test

### Test 1: Upload a Simple PDF
```bash
# Terminal 1: Start API
cd version3
uvicorn api:app --reload --port 8080

# Terminal 2: Test upload
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' > token.json

TOKEN=$(jq -r '.access_token' token.json)

curl -X POST http://localhost:8080/admin/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@/path/to/test.pdf"

# Should see: {"status":"success",...}
```

### Test 2: Check Files Saved
```bash
ls -la version3/uploads/
# Should show your PDF file
```

### Test 3: Download File Directly
```bash
curl "http://localhost:8080/api/documents/test.pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -o downloaded.pdf

file downloaded.pdf
# Should be: PDF document
```

### Test 4: Via Web UI
1. Open `http://localhost:5173/login`
2. Register as admin
3. Go to Admin → Documents tab
4. Upload a PDF
5. Go to Chat
6. Ask: "What's in the document?"
7. Click source badge
8. PDF should appear with page navigation

---

## Log Analysis

### API Logs (terminal running uvicorn)

**Success upload:**
```
INFO:     POST /admin/upload HTTP/1.1" 200 OK
```

**Failed upload:**
```
ERROR:     "POST /admin/upload" for 0.0.0.0
500 Internal Server Error
```

### Browser Console Logs

**Success:**
```
🔍 PDFViewer mounted with filename: document.pdf
📄 Attempting to load from: /api/documents/document.pdf
✅ PDF loaded successfully, pages: 10
```

**Failure:**
```
❌ PDF Load Error: Failed to fetch
```

---

## Environment Variables to Check

### `version3/config.py`
```python
OLLAMA_BASE = "http://www.munalbaraili.com"  # ← Must be reachable
CHROMA_HOST = "localhost"  # ← ChromaDB location
CHROMA_PORT = 8000
API_KEY = "mysecretkey"
```

### `version3/api.py`
```python
JWT_SECRET = "your-secret-key-change-in-production"
JWT_EXPIRATION_HOURS = 24
UPLOADS_DIR = Path(__file__).parent / "uploads"  # ← Must be writable
```

---

## Network Requests to Monitor

When you click a source badge, you should see:

1. **GET `/api/documents/filename.pdf`**
   - Headers: `Authorization: Bearer <token>`
   - Status: 200
   - Body: Binary PDF data

2. **If fails, check:**
   - Token valid (not expired)
   - File exists in `version3/uploads/`
   - API server is running
   - CORS headers present

---

## Reset Everything

If stuck, try a clean slate:

```bash
# Clear uploads
rm -rf version3/uploads/*

# Recreate directory
mkdir -p version3/uploads

# Test file write
touch version3/uploads/test.txt && rm version3/uploads/test.txt && echo "✓ Directory writable"

# Restart API
cd version3
uvicorn api:app --reload --port 8080 --log-level debug
```

---

## Still Not Working?

Share the output from:
```bash
# 1. Check files
ls -la version3/uploads/

# 2. Check API logs (paste last 20 lines from terminal)
# 3. Browser console errors (F12 → Console)
# 4. Network request details (F12 → Network → click source badge)
# 5. API response (F12 → Network → click /api/documents/* request → Response tab)
```
