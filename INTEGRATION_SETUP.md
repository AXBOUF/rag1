# Node Glow Login + version3 Integration Setup

This document describes how to run the integrated React frontend (Node Glow Login design) with the version3 RAG backend.

## Architecture

- **Backend**: FastAPI server at `http://localhost:8080` (wraps version3's Python modules)
- **Frontend**: React + Vite at `http://localhost:5173` (Node Glow Login design with real API calls)
- **Database**: ChromaDB at `http://localhost:8000` (for vector storage)
- **LLM/Embeddings**: Remote API at `http://www.munalbaraili.com` (Ollama)

## Prerequisites

1. **Python 3.10+** with venv activated for version3
2. **Node.js 18+** and npm for the React app
3. **ChromaDB running** on localhost:8000
4. **Remote LLM/embedding API** available at `http://www.munalbaraili.com`

## Setup Instructions

### 1. Start ChromaDB (if not already running)

```bash
docker run -p 8000:8000 chromadb/chroma
```

### 2. Start the FastAPI Backend

```bash
cd version3
source venv/bin/activate  # or activate your Python environment
uvicorn api:app --reload --port 8080
```

The API will be available at `http://localhost:8080`. Check health: `http://localhost:8080/health`

### 3. Start the React Frontend

```bash
cd "Node Glow Login"
npm install  # if not already done
npm run dev
```

The frontend will be available at `http://localhost:5173` (Vite default). Vite's dev proxy automatically forwards `/api/*` requests to `http://localhost:8080`.

## Testing the Integration

### Login/Register Flow

1. Open `http://localhost:5173/login`
2. **Register a new account**:
   - Email: `test@example.com`
   - Password: `password123`
   - Role: Choose any (employee/manager/admin)
3. Click "Create Account" → Switch to "Sign In" → Sign in with the credentials
4. JWT is stored in `localStorage` and you should be redirected to the dashboard

### Chat/Query Flow

1. On the dashboard, ensure you see:
   - Your username and role badge in the top-right
   - "Chat" tab active by default with sample messages
2. Type a question in the input box: *"What documents are available?"*
3. The query should:
   - Send to `POST /api/query` with your JWT token
   - Fetch embeddings and search ChromaDB
   - Return LLM response + sources
   - Display sources in the "Sauce —" section on the right

### Admin Features (if you registered as admin)

1. After logging in as admin, an "Admin" tab appears in the sidebar
2. **Documents tab**:
   - Upload one or more PDF files
   - Files are processed: PDF pages → chunks → classified → embedded
   - Total document count is displayed
3. **Users tab**:
   - View all registered users and their roles
4. **Logs tab**:
   - View audit logs of recent queries with user, role, status, etc.

## File Changes Summary

### Backend (version3)

- **New file**: `api.py` — FastAPI server
- **Unchanged**: All existing Python modules (auth, query, utils, etc.)

### Frontend (Node Glow Login)

- **New files**:
  - `src/lib/auth.ts` — JWT storage, login, register, user context
  - `src/lib/api.ts` — Typed fetch wrappers for all API endpoints
- **Modified files**:
  - `vite.config.ts` — Added dev proxy for `/api/*`
  - `src/routes/login.tsx` — Real API calls instead of fake navigation
  - `src/routes/dashboard.tsx` — Real queries, real admin panels, JWT-based role
- **Unchanged**: All UI components, CSS, 3D graphics

## API Endpoints

### Authentication

- `POST /auth/login` — `{username, password}` → `{access_token, user}`
- `POST /auth/register` — `{username, password, role}` → `{status, message}`
- `GET /auth/me` — (requires Authorization header) → current user info

### Query

- `POST /query` — `{query, top_k?}` → `{response, documents, metadatas, ...}`

### Admin (requires admin role)

- `GET /admin/users` → list of all users
- `GET /admin/stats` → `{total_documents}`
- `GET /admin/logs?limit=20` → `{logs: [...]}`
- `POST /admin/upload` — multipart form with PDF files

All authenticated endpoints require:
```
Authorization: Bearer <jwt_token>
```

## Environment Variables

### version3/config.py

- `OLLAMA_BASE` — Remote LLM API URL (default: `http://www.munalbaraili.com`)
- `CHROMA_HOST` / `CHROMA_PORT` — ChromaDB location
- `API_KEY` — API key for remote Ollama (default: `mysecretkey`)

### version3/api.py

- `JWT_SECRET` — Change `"your-secret-key-change-in-production"` in production
- `JWT_ALGORITHM` — Defaults to `"HS256"`
- `JWT_EXPIRATION_HOURS` — Token expiration time (default: 24)

## Troubleshooting

### "Cannot reach ChromaDB"

```bash
# Check if ChromaDB is running
curl http://localhost:8000/health

# If not, start it
docker run -p 8000:8000 chromadb/chroma
```

### "Invalid credentials" on login

- Verify the FastAPI server is running on port 8080
- Check that `POST /auth/login` is reachable: `curl -X POST http://localhost:8080/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}'`
- Default admin account: `admin` / `admin123`

### "Query failed" / "No response from LLM"

- Verify remote API is reachable: `curl http://www.munalbaraili.com/embed`
- Check API_KEY matches what the remote API expects

### React app not finding API (404 on `/api/*`)

- Ensure Vite dev server is running (`npm run dev`)
- Ensure FastAPI is on `http://localhost:8080`
- Check `vite.config.ts` has the proxy rule
- Reload the browser (Ctrl+Shift+R for hard refresh)

## Next Steps

1. **Production deployment**: 
   - Build React: `npm run build` → serves from `dist/`
   - Serve with FastAPI using `StaticFiles` middleware
   - Use environment variables for secrets (JWT_SECRET, API_KEY)

2. **Improve authentication**:
   - Replace plain-text password hashing with bcrypt
   - Add refresh tokens
   - Add session management

3. **Enhance RAG**:
   - Add document metadata filtering (date, author, etc.)
   - Implement document deletion
   - Add multi-document summary features
