# HILT - Human in the Loop LLM

A human-in-the-loop proxy for LLM requests. HILT intercepts API calls to language models and allows human operators to review, modify, or craft responses before they're returned to the client.

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ LLM Client  │────▶│  HILT Backend   │◀───▶│  Operator UI    │
│ (your app)  │◀────│  (FastAPI)      │     │  (React)        │
└─────────────┘     └─────────────────┘     └─────────────────┘
                           │
                    OpenAI-compatible
                         API
```

- **Backend**: FastAPI server exposing OpenAI-compatible endpoints
- **Frontend**: React dashboard for operators to handle requests
- **Communication**: WebSocket for real-time request/response flow

## Features

- OpenAI-compatible `/v1/chat/completions` endpoint
- Tool/function calling support
- Streaming responses
- JWT authentication for operators
- API key authentication for clients
- Rate limiting
- Request size limits
- Real-time WebSocket updates

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create environment file
cp .env.example .env

# Generate a password hash for your operator
python3 -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"

# Edit .env with your settings (see Configuration below)

# Install dependencies
pip install -e .

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8082
```

### 2. Frontend Setup

```bash
cd frontend

# Create environment file
cp .env.example .env

# Edit .env if using non-default backend URL

# Install dependencies
npm install

# Run development server
npm run dev
```

### 3. Test the Setup

```bash
# Health check
curl http://localhost:8082/health

# Send a test request (will wait for operator response)
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Authorization: Bearer hilt_sk_test123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (min 32 chars) | **required** |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `480` (8 hours) |
| `HILT_API_KEYS` | Comma-separated API keys for clients | **required** |
| `OPERATOR_USERNAME` | Operator login username | `admin` |
| `OPERATOR_PASSWORD_HASH` | Bcrypt hash of operator password | **required** |
| `REQUEST_TIMEOUT_SECONDS` | Request timeout | `300` (5 min) |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://localhost:5173` |
| `RATE_LIMIT_PER_MINUTE` | Max requests per minute per IP | `60` |
| `MAX_REQUEST_SIZE` | Max request body size in bytes | `10485760` (10MB) |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8082` |
| `VITE_WS_URL` | Backend WebSocket URL | `ws://localhost:8082/ws` |

## API Reference

### Authentication

**Client Authentication**: Use API key in Authorization header
```
Authorization: Bearer <your-api-key>
```

**Operator Authentication**: Login to get JWT token
```bash
curl -X POST http://localhost:8082/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat endpoint |
| `POST` | `/api/v1/auth/login` | Operator login |
| `GET` | `/api/v1/auth/me` | Get current operator |
| `WS` | `/ws?token=<jwt>` | WebSocket for operators |
| `GET` | `/health` | Health check |

### Chat Completions

```bash
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Authorization: Bearer <api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get weather for a location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {"type": "string"}
            },
            "required": ["location"]
          }
        }
      }
    ],
    "stream": false
  }'
```

### WebSocket Messages

**Incoming (from server):**
- `new_request` - New request waiting for response
- `request_cancelled` - Request was cancelled/timed out
- `stats_update` - Updated queue statistics
- `error` - Error message

**Outgoing (from operator):**
- `complete_response` - Submit complete response
- `start_response` - Start streaming response
- `response_chunk` - Send streaming chunk
- `add_tool_call` - Add tool call to response
- `finish_response` - Finish streaming response
- `reject_request` - Reject/cancel request

**Example: Respond with tool call**
```json
{
  "type": "complete_response",
  "data": {
    "request_id": "<uuid>",
    "content": null,
    "tool_calls": [
      {
        "id": "call_123",
        "function": {
          "name": "get_weather",
          "arguments": "{\"location\": \"San Francisco, CA\"}"
        }
      }
    ],
    "finish_reason": "tool_calls"
  }
}
```

## Security

- **Rate Limiting**: Login limited to 10/min, API requests limited to 60/min (configurable)
- **CORS**: Restricted to configured origins with specific methods/headers
- **Request Size**: Limited to 10MB by default
- **Token Storage**: Frontend uses sessionStorage (cleared on browser close)
- **Password Hashing**: Bcrypt for operator passwords

## Project Structure

```
hilt/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── core/            # Security, rate limiting
│   │   ├── models/          # Data models
│   │   ├── schemas/         # OpenAI schemas
│   │   ├── services/        # Business logic
│   │   ├── main.py          # FastAPI app
│   │   └── config.py        # Configuration
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── stores/          # Zustand stores
│   │   ├── hooks/           # Custom hooks
│   │   └── types/           # TypeScript types
│   ├── package.json
│   └── .env.example
└── tests/
    └── HILT_API.postman_collection.json
```

## Development

### Running Tests

```bash
# Import Postman collection from tests/ directory
# Or use the test script:
python test_request.py
```

### Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- Pydantic
- python-jose (JWT)
- slowapi (rate limiting)
- bcrypt

**Frontend:**
- React 19
- TypeScript
- Vite
- Zustand (state)
- TailwindCSS
- Monaco Editor

## License

MIT
