# PDF Viewer Feature - Source Document Display

## Overview

The source viewer now displays actual PDF files with a proper browser-based PDF viewer (similar to Edge/Chrome's PDF viewer), instead of just showing text previews.

## Architecture

### Backend (version3/api.py)

**New Features:**
- `POST /admin/upload` — Now saves uploaded PDFs to disk in `version3/uploads/` directory
- `GET /documents/{filename}` — Download/view a specific PDF file
- `GET /documents` — List all available documents with metadata (size, created_at)
- `GET /uploads/*` — Static file serving for PDFs

### Frontend (Node Glow Login)

**New Components:**
- `src/components/PDFViewer.tsx` — Full-featured PDF viewer component

**New Features:**
- `src/lib/api.ts` — Added `getDocuments()` function

**Updated Components:**
- `src/routes/dashboard.tsx` — Now uses PDFViewer instead of text preview
- Source modal replaced with full PDF viewer

## PDF Viewer Features

### Display Controls
- **Previous/Next buttons** — Navigate between pages
- **Page indicator** — Shows current page and total pages (e.g., "3 of 10")
- **Zoom controls** — Scale from 50% to 300%
- **Zoom percentage display** — Shows current zoom level

### Search & Navigation
- **CTRL+F support** — Press Ctrl+F or Cmd+F to focus search box
- **Find in document** — Search text within the PDF (highlights matches)
- **Text layer** — Selectable text from PDF (copy/paste support)
- **Annotation layer** — Displays PDF annotations and interactive elements

### Download & Controls
- **Download button** — Download the original PDF file
- **Close button** — Return to chat view
- **Edge-style header** — Matches browser PDF viewer UI

## How It Works

1. **Upload Phase**:
   - User clicks "Upload Documents" in Admin panel
   - PDFs are uploaded via `POST /api/admin/upload`
   - Backend processes PDFs:
     - Saves to `version3/uploads/{filename}`
     - Extracts pages and creates embeddings
     - Classifies sensitivity levels
     - Stores in ChromaDB
   - Files remain on disk for viewing

2. **Query Phase**:
   - User asks a question
   - RAG retrieves relevant chunks from ChromaDB
   - Returns metadata including filename and page number
   - Sources are displayed as clickable "Sauce" badges

3. **View Phase**:
   - User clicks a source badge
   - Dashboard requests the PDF from `/api/documents/{filename}`
   - React-PDF loads and displays the PDF
   - User can navigate pages, zoom, search, and download

## File Structure

```
version3/
├── api.py                 # FastAPI with PDF endpoints
├── uploads/               # Directory for storing PDFs (auto-created)
│   ├── document1.pdf
│   ├── document2.pdf
│   └── ...

Node Glow Login/
├── src/
│   ├── components/
│   │   └── PDFViewer.tsx  # New PDF viewer component
│   ├── lib/
│   │   └── api.ts         # Updated with getDocuments()
│   └── routes/
│       └── dashboard.tsx  # Updated to use PDFViewer
```

## Technical Details

### React-PDF Library
- Uses `react-pdf` (built on pdfjs-dist)
- Renders PDF pages as canvas + text layer
- Supports CTRL+F browser search
- Responsive zoom with text layer rendering

### Worker Configuration
```typescript
pdfjs.GlobalWorkerOptions.workerSrc = 
  `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`
```

### Styling
- Edge-like header with file name and controls
- Responsive footer with page navigation and zoom
- Background gradient for paper effect
- Seamless integration with Hungry Jacks color scheme

## Usage Example

### Register & Upload
```bash
# 1. Register as admin
POST /api/auth/register
{ "username": "admin", "password": "admin123", "role": "admin" }

# 2. Login
POST /api/auth/login
{ "username": "admin", "password": "admin123" }
# Returns: { "access_token": "...", "user": {...} }

# 3. Upload PDFs
POST /api/admin/upload
Headers: { "Authorization": "Bearer <token>" }
Body: FormData with multiple PDF files

# Files are saved to:
# version3/uploads/document1.pdf
# version3/uploads/document2.pdf
# etc.
```

### Query & View
```bash
# 1. Query
POST /api/query
{ "query": "What's in document1.pdf?", "top_k": 3 }

# Response includes metadatas:
{
  "metadatas": [
    {
      "filename": "document1.pdf",
      "page": 0,
      "sensitivity_level": "public",
      ...
    }
  ]
}

# 2. Click source badge → PDFViewer loads
# 3. Browser requests:
GET /api/documents/document1.pdf
# Returns the actual PDF file
```

## CTRL+F / Search

The PDF viewer supports full-text search:
1. Press **Ctrl+F** (Windows/Linux) or **Cmd+F** (Mac)
2. Search box appears in the header
3. Type to search the PDF
4. Matches are highlighted automatically

## Keyboard Shortcuts

| Key | Action |
|---|---|
| Ctrl+F / Cmd+F | Focus search box |
| Up Arrow | Previous page |
| Down Arrow | Next page |
| + Button | Zoom in |
| − Button | Zoom out |

## Limitations & Considerations

1. **OCR**: PDFs without embedded text won't have searchable text (use extracted text layer from RAG response)
2. **Scanned PDFs**: Work but require OCR (not included by default)
3. **Large PDFs**: May be slow on lower-end machines (consider compression)
4. **File Size**: No limit enforced, but large files will impact upload/download performance

## Future Enhancements

- [ ] Highlight search terms from RAG query in PDF
- [ ] Sidebar with PDF bookmarks/thumbnails
- [ ] Annotation tools (highlighting, notes)
- [ ] Print to PDF
- [ ] Signature verification for signed PDFs
- [ ] Full-text OCR for scanned documents
- [ ] Batch download of multiple PDFs

## Error Handling

### "Document not found"
- PDF may have been deleted
- Check `/api/documents` to list available files
- Re-upload the document if needed

### "Error loading PDF"
- PDF may be corrupted
- Try re-uploading
- Check browser console for details

### "CORS error"
- Ensure FastAPI CORS middleware allows frontend origin
- Check `vite.config.ts` proxy configuration

## Production Deployment

### Before Deploying
1. Change `JWT_SECRET` in `api.py` to a strong random value
2. Set up persistent storage for uploads (not local disk)
3. Consider cloud storage (AWS S3, Azure Blob, Google Cloud Storage)
4. Set file size limits on uploads
5. Implement cleanup for old/deleted documents

### Example S3 Integration
```python
# Replace local file storage with S3
import boto3

s3 = boto3.client('s3')
s3.upload_file(file_path, 'bucket-name', f'pdfs/{filename}')
```

## Dependencies

New packages installed:
```
react-pdf
pdfjs-dist (installed automatically with react-pdf)
```

Existing packages used:
```
FastAPI (static files serving)
Vite (proxy configuration)
TanStack Router (routing)
```
