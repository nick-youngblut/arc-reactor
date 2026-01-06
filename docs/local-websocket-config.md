# Local Development: WebSocket Configuration

## Issue
When running the app locally with separate dev servers (backend on port 8000, frontend on port 3000), the AI Agent Chat WebSocket connection fails because of a URL mismatch.

## Why This Happens

### Production vs Development Architecture

**Production (Docker/Cloud Run):**
- FastAPI serves the static Next.js build
- Everything runs on one port (e.g., 8000)
- WebSocket path: `ws://localhost:8000/ws/chat`
- API path: `http://localhost:8000/api/...`
- Frontend uses relative URLs like `/api` and `/ws/chat`

**Local Development:**
- Backend: `uvicorn` on port 8000
- Frontend: `npm run dev` on port 3000
- Separate processes, separate ports
- Frontend needs absolute URLs to reach the backend

### The URL Mismatch

**Without configuration:**
- Frontend constructs WebSocket URL based on its own origin: `ws://localhost:3000/api/chat/ws`
- Backend WebSocket endpoint is at: `ws://localhost:8000/ws/chat`
- Connection fails silently because Next.js dev server doesn't handle WebSocket requests

**Backend WebSocket Route:**
```python
# backend/api/routes/chat.py
@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    ...
```

**Backend Router Registration:**
```python
# backend/main.py
app.include_router(chat_router)  # No prefix, so endpoint is /ws/chat
```

## Solution

### 1. Create `frontend/.env.local`

```bash
# Backend WebSocket URL for local development
NEXT_PUBLIC_CHAT_WS_URL=ws://localhost:8000/ws/chat

# Backend API URL for local development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Restart the Frontend Dev Server

After creating or modifying `.env.local`, you **must** restart:

```bash
# Stop current dev server (Ctrl+C), then:
cd frontend && npm run dev
```

### 3. Verify the Configuration

Open browser DevTools Console and look for:
- WebSocket connection to `ws://localhost:8000/ws/chat`
- No connection errors
- "connected" message from backend

## How the Code Uses These Variables

### WebSocket URL (`useAgentChat.ts`)
```typescript
function buildWebSocketUrl() {
  if (typeof window === 'undefined') return null;
  const envUrl = process.env.NEXT_PUBLIC_CHAT_WS_URL;  // Checks env var first
  if (envUrl) return envUrl;
  // Fallback to relative URL (for production)
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${protocol}://${window.location.host}/api/chat/ws`;
}
```

### API Client (`lib/api.ts`)
```typescript
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL 
    ? `${process.env.NEXT_PUBLIC_API_URL}/api`
    : '/api',  // Fallback to relative URL (for production)
  headers: {
    'Content-Type': 'application/json'
  }
});
```

## Troubleshooting

### Chat messages disappear but nothing happens
- Check if `.env.local` exists in `frontend/` directory
- Verify `NEXT_PUBLIC_CHAT_WS_URL=ws://localhost:8000/ws/chat`
- Restart the frontend dev server
- Check browser DevTools Console for WebSocket connection errors

### Backend shows no WebSocket connections
- Verify backend is running on port 8000
- Check backend logs for startup messages
- Ensure no firewall blocking localhost:8000
- Try accessing `http://localhost:8000/docs` to confirm backend is responsive

### Still not working after restart
- Clear browser cache
- Check browser DevTools > Network tab > WS filter
- Verify the WebSocket URL in the request
- Look for CORS errors in browser console

## Files Involved

- `frontend/.env.local` - Local development environment variables (gitignored)
- `frontend/.env.example` - Template for environment variables (tracked in git)
- `frontend/hooks/useAgentChat.ts` - WebSocket connection logic
- `frontend/lib/api.ts` - REST API client configuration
- `backend/api/routes/chat.py` - WebSocket endpoint handler
- `backend/main.py` - FastAPI app and router registration

