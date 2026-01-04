# HILT API Tests

This folder contains test resources for the HILT API.

## Postman Collection

### Import into Postman

1. Open Postman
2. Click "Import" in the top left
3. Select `HILT_API.postman_collection.json`
4. The collection will appear in your sidebar

### Available Test Requests

#### Authentication
- **Login** - Get JWT token for operator dashboard

#### Health Check
- **Health Check** - Verify backend is running and get stats

#### Chat Completions
- **Simple Chat (No Tools)** - Basic chat completion without tools
- **Chat with Weather Tool** - Request weather information
- **Chat with Multiple Tools** - Flight booking + weather check
- **Chat with SQL Tool** - Database query execution (requires approval)
- **Chat with File Operations** - File deletion (requires approval)
- **Chat with Email Tool** - Send email (requires approval)

### How to Use

1. **Start the backend server**:
   ```bash
   cd backend
   source .venv/bin/activate
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8082
   ```

2. **Start the frontend** (for operator UI):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Login to operator UI**:
   - Go to http://localhost:5173
   - Username: `admin`
   - Password: `admin`

4. **Send requests from Postman**:
   - Each request will appear in the operator UI
   - Respond through the UI to complete the request
   - Postman will receive the response

### API Key

All chat completion requests use the API key: `hilt_sk_test123`

This is configured in the Authorization header:
```
Authorization: Bearer hilt_sk_test123
```

### Expected Behavior

When you send a chat completion request:
1. Request appears immediately in the operator UI
2. Operator sees full request details (model, messages, tools)
3. Operator composes response (text and/or tool calls)
4. Operator clicks "Submit Response"
5. Postman receives OpenAI-compatible response

### Response Format

Successful responses follow the OpenAI Chat Completions format:

```json
{
  "id": "chatcmpl-xxxxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response content here",
        "tool_calls": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### Timeout

Requests timeout after 300 seconds (5 minutes) by default. Make sure to respond through the UI before the timeout expires.
