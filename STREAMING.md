# Streaming Response Implementation

This document describes the streaming response feature for the KidsGPT chat API.

## Overview

The streaming response feature allows clients to receive AI responses incrementally as they are generated, providing a better user experience with faster perceived response times.

## Endpoints

### Regular Chat (Non-Streaming)
- **Endpoint**: `POST /api/kid/chat`
- **Response**: Complete response returned after AI finishes generating
- **Use case**: Simple integrations, batch processing

### Streaming Chat
- **Endpoint**: `POST /api/kid/chat/stream`
- **Response**: Server-Sent Events (SSE) stream
- **Use case**: Interactive chat UI with real-time response display

## How to Use Streaming

### Request

Send a POST request to `/api/kid/chat/stream` with the same payload as the regular chat endpoint:

```json
{
  "message": "What is the solar system?",
  "session_id": "optional-session-uuid"
}
```

**Headers Required:**
- `Authorization: Bearer <JWT_TOKEN>`
- `Content-Type: application/json`

### Response Format

The endpoint uses Server-Sent Events (SSE) format. You'll receive multiple events:

#### Event Types

1. **user_message** - Confirms user message was saved
```
event: user_message
data: {"id": "message-uuid", "content": "What is the solar system?", "session_id": "session-uuid"}
```

2. **chunk** - AI response chunks (multiple events)
```
event: chunk
data: {"content": "The "}

event: chunk
data: {"content": "solar "}

event: chunk
data: {"content": "system "}
```

3. **done** - Complete response saved
```
event: done
data: {"id": "message-uuid", "content": "The solar system is...", "session_id": "session-uuid", "session_title": "Learning about space"}
```

4. **blocked** - Message was blocked by content filter
```
event: blocked
data: {"block_reason": "Content not appropriate", "message_id": "message-uuid", "session_id": "session-uuid", "session_title": "New Chat"}
```

5. **error** - An error occurred
```
event: error
data: {"error": "Error message"}
```

### Client Implementation Examples

#### JavaScript (Fetch API + EventSource)

```javascript
async function sendStreamingMessage(message, sessionId, token) {
  const response = await fetch('http://localhost:8000/api/kid/chat/stream', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message, session_id: sessionId })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop(); // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('event:')) {
        const eventMatch = line.match(/event: (\w+)/);
        const dataMatch = line.match(/data: (.+)/);

        if (eventMatch && dataMatch) {
          const eventType = eventMatch[1];
          const data = JSON.parse(dataMatch[1]);

          switch (eventType) {
            case 'user_message':
              // User message confirmed
              console.log('Message sent:', data);
              break;
            case 'chunk':
              // Append chunk to UI
              appendToMessage(data.content);
              break;
            case 'done':
              // Mark message as complete
              finalizeMessage(data.id, data.session_id, data.session_title);
              break;
            case 'blocked':
              // Show blocked message
              showBlocked(data.block_reason);
              break;
            case 'error':
              // Show error
              showError(data.error);
              break;
          }
        }
      }
    }
  }
}
```

#### Python (httpx)

```python
import httpx
import json

async def stream_chat(message: str, session_id: str, token: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            'http://localhost:8000/api/kid/chat/stream',
            headers={'Authorization': f'Bearer {token}'},
            json={'message': message, 'session_id': session_id}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('event:'):
                    event_type = line.split(': ')[1]
                elif line.startswith('data:'):
                    data = json.loads(line.split(': ', 1)[1])

                    if event_type == 'chunk':
                        print(data['content'], end='', flush=True)
                    elif event_type == 'done':
                        print(f"\n[Message ID: {data['id']}]")
                        print(f"[Session: {data['session_title']}]")
                    elif event_type == 'blocked':
                        print(f"Blocked: {data['block_reason']}")
                    elif event_type == 'error':
                        print(f"Error: {data['error']}")
```

#### cURL (for testing)

```bash
curl -N -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message":"What is the solar system?"}' \
     http://localhost:8000/api/kid/chat/stream
```

## Benefits

1. **Better UX**: Users see responses appear in real-time
2. **Faster perceived response**: First tokens appear quickly
3. **Same content filtering**: All safety features still apply
4. **Database consistency**: Messages saved the same way
5. **Error handling**: Errors streamed to client immediately
6. **Session support**: Full session management and title generation

## Implementation Details

### Backend Architecture

1. **AI Service Layer** (`app/services/ai_service.py`)
   - `generate_response_stream()` method added to all providers
   - OpenAI: Uses `stream=True` parameter
   - Gemini: Uses `stream=True` parameter
   - Mock: Simulates streaming with word-by-word output

2. **API Endpoint** (`app/api/v1/kid.py`)
   - New `/chat/stream` endpoint
   - Uses FastAPI's `StreamingResponse`
   - Same content filtering as regular chat
   - SSE format for browser compatibility
   - Session management and title generation

3. **Database**
   - User message saved immediately
   - AI response accumulated during streaming
   - Complete response saved when streaming finishes
   - Same Message model used for both streaming and non-streaming
   - Session metadata updated (last_message_at, message_count, title)

### Content Filtering

Content filtering happens **before** streaming starts:
- Blocked messages never reach the AI
- Blocked event sent immediately to client
- No tokens streamed for blocked content

### Session Management

Streaming endpoint supports full session management:
- Create new sessions automatically if no session_id provided
- Verify session ownership before streaming
- Update session metadata (last message time, message count)
- Generate AI-powered session titles after first message
- Return session_id and session_title in events

### Error Handling

Errors are caught and streamed as error events:
- Network errors
- AI provider errors
- Rate limiting
- Database errors
- Session authorization errors

## Migration Guide

Existing clients using `/api/kid/chat` will continue to work. To add streaming support:

1. Detect if client supports SSE (modern browsers do)
2. Use `/chat/stream` for supported clients
3. Fall back to `/chat` for older clients
4. Handle both response formats in your UI

## Performance Considerations

- Streaming uses Server-Sent Events (one-way from server to client)
- Connection stays open until response completes
- Database writes happen at the same frequency as non-streaming
- Memory usage: Response is accumulated server-side for database storage
- Insights processing happens after streaming completes

## Security

- Same JWT authentication required
- Same content filtering applied
- Same rate limiting rules
- Messages logged identically to non-streaming
- Session authorization verified

## Testing

Test the streaming endpoint:

```bash
# Using the mock provider (no API key needed)
export AI_PROVIDER=mock

# Start the server
cd backend
uvicorn app.main:app --reload

# In another terminal, test with curl
curl -N -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message":"Hello!"}' \
     http://localhost:8000/api/kid/chat/stream
```

## Troubleshooting

**Issue**: Connection closes immediately
- **Solution**: Check that your client supports SSE or uses streaming HTTP clients

**Issue**: No chunks received
- **Solution**: Verify AI provider is configured correctly and API keys are set

**Issue**: Chunks arrive slowly
- **Solution**: This is normal for OpenAI/Gemini based on their response generation speed

**Issue**: CORS errors in browser
- **Solution**: Ensure CORS settings in `app/config.py` include your frontend origin

**Issue**: Session not found error
- **Solution**: Verify the session_id belongs to the authenticated child, or omit it to create a new session
