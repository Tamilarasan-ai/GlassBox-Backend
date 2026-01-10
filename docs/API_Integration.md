# Frontend Integration API Documentation

> **Complete Guide for Integrating with GlassBox Agent Backend**

This document provides everything frontend developers need to integrate with the GlassBox Agent Backend API. It covers authentication, all available endpoints, real-time streaming, error handling, and best practices.

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
   - [Chat Endpoints](#chat-endpoints)
   - [Trace Endpoints](#trace-endpoints)
   - [Session Endpoints](#session-endpoints)
   - [Analytics Endpoints](#analytics-endpoints)
   - [Health Endpoints](#health-endpoints)
4. [Server-Sent Events (SSE)](#server-sent-events-sse)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Code Examples](#code-examples)
8. [Best Practices](#best-practices)

---

## 🚀 Getting Started

### Base URL

```
Production: https://your-domain.com
Development: http://localhost:8000
```

### Required Headers

All API requests require the following headers:

```javascript
{
  "Authorization": "Bearer <client_uuid>",
  "X-API-Key": "<your_api_key>",
  "Content-Type": "application/json"
}
```

### Optional Headers

```javascript
{
  "X-Device-Fingerprint": "<device_fingerprint_hash>"  // For enhanced security
}
```

---

## 🔐 Authentication

GlassBox uses a **Guest User Authentication** system with UUID-based tokens and optional device fingerprinting.

### Client ID Generation

The client must generate and store a UUID on first visit:

```javascript
// Check if client_id exists in localStorage
let clientId = localStorage.getItem('glassbox_client_id');

if (!clientId) {
  // Generate new UUID v4
  clientId = crypto.randomUUID();
  localStorage.setItem('glassbox_client_id', clientId);
}
```

### Device Fingerprinting (Optional)

For enhanced security, you can generate a device fingerprint:

```javascript
async function generateFingerprint() {
  const components = [
    navigator.userAgent,
    navigator.language,
    new Date().getTimezoneOffset(),
    screen.colorDepth,
    screen.width + 'x' + screen.height,
    navigator.hardwareConcurrency || 'unknown'
  ];
  
  const fingerprint = components.join('|');
  
  // Hash the fingerprint (using Web Crypto API)
  const encoder = new TextEncoder();
  const data = encoder.encode(fingerprint);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  return hashHex;
}
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant Frontend
    participant Backend
    participant Database
    
    Frontend->>Frontend: Check localStorage for client_id
    alt No client_id
        Frontend->>Frontend: Generate UUID
        Frontend->>Frontend: Save to localStorage
    end
    Frontend->>Frontend: Generate device fingerprint (optional)
    Frontend->>Backend: Request with Bearer token
    Backend->>Database: Get or create guest user
    Database-->>Backend: Return guest user
    Backend->>Backend: Validate fingerprint & rate limits
    Backend-->>Frontend: Return response or error
```

### Security Features

- **Rate Limiting**: 60 requests per minute, 1000 per hour per guest
- **Device Fingerprinting**: Fuzzy matching with 70% similarity threshold (default)
- **IP Change Detection**: Logs for security monitoring
- **Automatic Blocking**: Configurable blocking for suspicious activity

---

## 📡 API Endpoints

### Chat Endpoints

#### POST `/api/v1/chat/stream` - Stream Chat (Recommended)

Real-time streaming chat using Server-Sent Events (SSE).

**Request:**
```http
POST /api/v1/chat/stream HTTP/1.1
Authorization: Bearer 123e4567-e89b-12d3-a456-426614174000
X-API-Key: your_api_key
Content-Type: application/json

{
  "message": "Calculate 10 + 5",
  "user_id": "optional_user_identifier",
  "max_iterations": 10
}
```

**Response:** SSE Stream
```
event: message
data: {"type": "start", "session_id": "uuid", "trace_id": "uuid"}

event: message
data: {"type": "thought", "content": {"thought": "I need to use the calculator"}}

event: message
data: {"type": "tool_call", "name": "calculator", "args": {"expression": "10 + 5"}}

event: message
data: {"type": "tool_result", "result": "15"}

event: message
data: {"type": "response", "content": "The answer is 15"}

event: message
data: {"type": "complete", "success": true, "trace_id": "uuid"}
```

**Event Types:**
- `start` - Streaming started
- `thought` - Agent reasoning step
- `tool_call` - Tool being invoked
- `tool_result` - Tool execution result
- `response` - Final/intermediate response
- `complete` - Execution finished
- `error` - Error occurred

#### POST `/api/v1/chat` - Sync Chat (Deprecated)

Non-streaming synchronous chat. Returns complete response after execution.

**Request:**
```http
POST /api/v1/chat HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
Content-Type: application/json

{
  "message": "What is 50 * 10?",
  "user_id": "optional_user_id",
  "max_iterations": 10
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "response": "The result is 500",
  "steps_taken": 4,
  "status": "completed"
}
```

---

### Trace Endpoints

#### GET `/api/v1/traces` - List Traces

Get paginated list of all traces.

**Request:**
```http
GET /api/v1/traces?limit=10&offset=0&session_id=optional_uuid HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
```

**Query Parameters:**
- `limit` (int, optional): Max traces to return (1-100, default: 50)
- `offset` (int, optional): Skip first N traces (default: 0)
- `session_id` (uuid, optional): Filter by session

**Response:**
```json
{
  "traces": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "agent_id": "uuid",
      "user_input": "Calculate 10 + 5",
      "final_output": "The answer is 15",
      "run_name": null,
      "total_tokens": 129,
      "total_cost": "0.000015",
      "latency_ms": 2881,
      "is_successful": true,
      "error_message": null,
      "environment": "production",
      "created_at": "2026-01-10T06:15:49.485Z",
      "completed_at": "2026-01-10T06:15:52.366Z"
    }
  ],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

#### GET `/api/v1/traces/{trace_id}` - Get Trace Detail

Get detailed trace with all steps.

**Request:**
```http
GET /api/v1/traces/123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
```

**Response:**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "agent_id": "uuid",
  "user_input": "Calculate 10 + 5",
  "final_output": "The answer is 15",
  "run_name": null,
  "total_tokens": 129,
  "total_cost": "0.000015",
  "latency_ms": 2881,
  "is_successful": true,
  "error_message": null,
  "system_prompt_snapshot": "You are a helpful assistant...",
  "model_config_snapshot": {
    "model": "gemini-2.5-flash",
    "temperature": 0.1
  },
  "tags": [],
  "environment": "production",
  "created_at": "2026-01-10T06:15:49.485Z",
  "completed_at": "2026-01-10T06:15:52.366Z",
  "steps": [
    {
      "id": "uuid",
      "sequence_order": 1,
      "step_type": "thought",
      "step_name": "Reasoning",
      "input_payload": null,
      "output_payload": {
        "thought": "I need to use the calculator",
        "reasoning": "Math operation required"
      },
      "latency_ms": 2,
      "tokens": 0,
      "cost_usd": "0.000000",
      "is_error": false,
      "error_message": null,
      "started_at": "2026-01-10T06:15:49.485Z",
      "completed_at": "2026-01-10T06:15:49.487Z"
    },
    {
      "id": "uuid",
      "sequence_order": 2,
      "step_type": "tool_call",
      "step_name": "calculator",
      "input_payload": {
        "expression": "10 + 5"
      },
      "output_payload": null,
      "latency_ms": 15,
      "tokens": 0,
      "cost_usd": "0.000000",
      "is_error": false,
      "error_message": null,
      "started_at": "2026-01-10T06:15:49.487Z",
      "completed_at": "2026-01-10T06:15:49.502Z"
    },
    {
      "id": "uuid",
      "sequence_order": 3,
      "step_type": "tool_result",
      "step_name": "calculator",
      "input_payload": null,
      "output_payload": {
        "result": "15"
      },
      "latency_ms": 3,
      "tokens": 0,
      "cost_usd": "0.000000",
      "is_error": false,
      "error_message": null,
      "started_at": "2026-01-10T06:15:49.502Z",
      "completed_at": "2026-01-10T06:15:49.505Z"
    },
    {
      "id": "uuid",
      "sequence_order": 4,
      "step_type": "response",
      "step_name": "Final Answer",
      "input_payload": null,
      "output_payload": {
        "content": "The answer is 15"
      },
      "latency_ms": 8,
      "tokens": 129,
      "cost_usd": "0.000015",
      "is_error": false,
      "error_message": null,
      "started_at": "2026-01-10T06:15:49.505Z",
      "completed_at": "2026-01-10T06:15:49.513Z"
    }
  ]
}
```

**Step Types:**
- `thought` - Agent reasoning/thinking
- `tool_call` - Tool invocation
- `tool_result` - Tool execution result
- `llm_response` - LLM-generated response

#### POST `/api/v1/traces/{trace_id}/replay` - Replay Trace

Re-execute a trace with the same input.

**Request:**
```http
POST /api/v1/traces/123e4567-e89b-12d3-a456-426614174000/replay HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
```

**Response:**
```json
{
  "original_trace_id": "uuid",
  "new_trace_id": "uuid",
  "message": "Trace replayed successfully"
}
```

---

### Session Endpoints

#### GET `/api/v1/sessions/{session_id}` - Get Session

Get session details with all traces.

**Request:**
```http
GET /api/v1/sessions/123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "string",
  "agent_id": "uuid",
  "user_input": "string",
  "final_response": "string",
  "status": "active",
  "created_at": "2026-01-10T06:15:49.485Z",
  "updated_at": "2026-01-10T06:15:49.485Z",
  "traces": []
}
```

#### GET `/api/v1/sessions/{session_id}/traces` - Get Session Traces

Get all traces for a specific session.

**Request:**
```http
GET /api/v1/sessions/123e4567-e89b-12d3-a456-426614174000/traces HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
```

**Response:** Returns array of traces (same format as trace list).

---

### Analytics Endpoints

#### GET `/api/v1/analytics/tokens/me` - Get My Token Usage

Get token usage statistics for the current guest user.

**Request:**
```http
GET /api/v1/analytics/tokens/me?days=30 HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
```

**Query Parameters:**
- `days` (int, optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "total_tokens": 12450,
  "total_cost_usd": "0.001867",
  "trace_count": 45,
  "avg_tokens_per_trace": 276,
  "period_days": 30
}
```

#### GET `/api/v1/analytics/tokens/session/{session_id}` - Get Session Token Usage

Get token usage for a specific session.

**Request:**
```http
GET /api/v1/analytics/tokens/session/123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
```

**Response:**
```json
{
  "session_id": "uuid",
  "total_tokens": 850,
  "total_cost_usd": "0.000127",
  "trace_count": 3
}
```

#### GET `/api/v1/analytics/tokens/trace/{trace_id}` - Get Trace Token Breakdown

Get detailed token breakdown for a trace.

**Request:**
```http
GET /api/v1/analytics/tokens/trace/123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
```

**Response:**
```json
{
  "trace_id": "uuid",
  "total_tokens": 129,
  "total_cost_usd": "0.000015",
  "steps": [
    {
      "step_name": "Reasoning",
      "tokens": 0,
      "cost_usd": "0.000000"
    },
    {
      "step_name": "calculator",
      "tokens": 0,
      "cost_usd": "0.000000"
    },
    {
      "step_name": "Final Answer",
      "tokens": 129,
      "cost_usd": "0.000015"
    }
  ]
}
```

#### GET `/api/v1/analytics/tokens/global` - Get Global Token Stats

Get system-wide token usage statistics (may be restricted).

**Request:**
```http
GET /api/v1/analytics/tokens/global?days=30 HTTP/1.1
Authorization: Bearer <client_uuid>
X-API-Key: <api_key>
```

**Response:**
```json
{
  "total_tokens": 1245000,
  "total_cost_usd": "186.750",
  "total_traces": 4500,
  "avg_tokens_per_trace": 276,
  "period_days": 30,
  "unique_users": 150
}
```

---

### Health Endpoints

#### GET `/` - Root

Basic health check.

**Request:**
```http
GET / HTTP/1.1
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

#### GET `/health` - Detailed Health

Detailed health check with database status.

**Request:**
```http
GET /health HTTP/1.1
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-01-10T06:15:49.485Z"
}
```

---

## 📡 Server-Sent Events (SSE)

The `/api/v1/chat/stream` endpoint uses Server-Sent Events for real-time streaming.

### JavaScript Example

```javascript
async function streamChat(message) {
  const clientId = localStorage.getItem('glassbox_client_id');
  
  const response = await fetch('http://localhost:8000/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${clientId}`,
      'X-API-Key': 'your_api_key',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      max_iterations: 10
    })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));
        
        switch (data.type) {
          case 'start':
            console.log('Session started:', data.session_id);
            break;
          case 'thought':
            console.log('Agent thinking:', data.content);
            break;
          case 'tool_call':
            console.log('Calling tool:', data.name, data.args);
            break;
          case 'tool_result':
            console.log('Tool result:', data.result);
            break;
          case 'response':
            console.log('Response:', data.content);
            break;
          case 'complete':
            console.log('Completed:', data.trace_id);
            break;
          case 'error':
            console.error('Error:', data.error);
            break;
        }
      }
    }
  }
}
```

### React Hook Example

```javascript
import { useEffect, useState } from 'react';

function useStreamChat() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  
  const streamChat = async (message) => {
    setIsStreaming(true);
    setMessages([]);
    
    const clientId = localStorage.getItem('glassbox_client_id');
    
    const response = await fetch('http://localhost:8000/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${clientId}`,
        'X-API-Key': process.env.REACT_APP_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6));
            setMessages(prev => [...prev, data]);
            
            if (data.type === 'complete' || data.type === 'error') {
              setIsStreaming(false);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setIsStreaming(false);
    }
  };
  
  return { messages, isStreaming, streamChat };
}
```

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Access blocked (rate limit, banned user) |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Invalid request body |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |

### Error Response Format

```json
{
  "detail": "Error message",
  "error_code": "OPTIONAL_ERROR_CODE"
}
```

### Validation Errors (422)

```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Common Error Scenarios

#### 1. Missing Authentication
```json
{
  "detail": "Missing guest token. Please provide Authorization: Bearer {client_id}"
}
```

#### 2. Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Try again at 2026-01-10T06:16:49Z"
}
```

**Response Headers:**
```
Retry-After: 60
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2026-01-10T06:16:49Z
```

#### 3. Blocked User
```json
{
  "detail": "Access blocked: Account suspended"
}
```

#### 4. Device Fingerprint Mismatch (Strict Mode)
```json
{
  "detail": "Device fingerprint verification failed. Similarity: 45%, Required: 70%"
}
```

### Error Handling Example

```javascript
async function apiRequest(endpoint, options) {
  try {
    const response = await fetch(endpoint, options);
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Redirect to login or regenerate client_id
          console.error('Authentication failed:', error.detail);
          break;
        case 403:
          // User blocked
          console.error('Access forbidden:', error.detail);
          break;
        case 429:
          // Rate limited - extract retry time
          const retryAfter = response.headers.get('Retry-After');
          console.error('Rate limited, retry after:', retryAfter);
          break;
        case 422:
          // Validation error - show field errors
          console.error('Validation errors:', error.detail);
          break;
        default:
          console.error('API error:', error.detail);
      }
      
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}
```

---

## 🚦 Rate Limiting

### Limits

- **Per Minute**: 60 requests
- **Per Hour**: 1000 requests
- **Scope**: Per guest user (client_id)

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 2026-01-10T06:16:49Z
```

### Handling Rate Limits

```javascript
function parseRateLimitHeaders(response) {
  return {
    limit: parseInt(response.headers.get('X-RateLimit-Limit')),
    remaining: parseInt(response.headers.get('X-RateLimit-Remaining')),
    reset: response.headers.get('X-RateLimit-Reset')
  };
}

async function makeRequest(url, options) {
  const response = await fetch(url, options);
  const rateLimit = parseRateLimitHeaders(response);
  
  // Warn if approaching limit
  if (rateLimit.remaining < 10) {
    console.warn(`Low rate limit: ${rateLimit.remaining} requests remaining`);
  }
  
  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After'));
    console.log(`Rate limited. Retrying after ${retryAfter} seconds`);
    
    // Wait and retry
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    return makeRequest(url, options);
  }
  
  return response.json();
}
```

---

## 💻 Code Examples

### Complete Integration Example

```javascript
class GlassBoxClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.clientId = this.getOrCreateClientId();
  }
  
  getOrCreateClientId() {
    let clientId = localStorage.getItem('glassbox_client_id');
    if (!clientId) {
      clientId = crypto.randomUUID();
      localStorage.setItem('glassbox_client_id', clientId);
    }
    return clientId;
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.clientId}`,
      'X-API-Key': this.apiKey,
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    const response = await fetch(url, {
      ...options,
      headers
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return response.json();
  }
  
  async streamChat(message, onMessage) {
    const response = await fetch(`${this.baseUrl}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.clientId}`,
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.substring(6));
          onMessage(data);
        }
      }
    }
  }
  
  async getTraces(limit = 50, offset = 0) {
    return this.request(`/api/v1/traces?limit=${limit}&offset=${offset}`);
  }
  
  async getTraceDetail(traceId) {
    return this.request(`/api/v1/traces/${traceId}`);
  }
  
  async replayTrace(traceId) {
    return this.request(`/api/v1/traces/${traceId}/replay`, {
      method: 'POST'
    });
  }
  
  async getMyTokenUsage(days = 30) {
    return this.request(`/api/v1/analytics/tokens/me?days=${days}`);
  }
}

// Usage
const client = new GlassBoxClient('http://localhost:8000', 'your_api_key');

// Stream chat
client.streamChat('Calculate 10 + 5', (data) => {
  console.log('Event:', data.type, data);
});

// Get traces
const traces = await client.getTraces(10, 0);
console.log('Traces:', traces);

// Get trace detail
const detail = await client.getTraceDetail(traces.traces[0].id);
console.log('Detail:', detail);
```

---

## ✅ Best Practices

### 1. Client ID Management

```javascript
// ✅ Good: Persistent client ID
const clientId = localStorage.getItem('glassbox_client_id') || 
                 (() => {
                   const id = crypto.randomUUID();
                   localStorage.setItem('glassbox_client_id', id);
                   return id;
                 })();

// ❌ Bad: Regenerating on every request
const clientId = crypto.randomUUID();
```

### 2. Error Recovery

```javascript
// ✅ Good: Handle rate limits gracefully
async function makeRequestWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      
      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        continue;
      }
      
      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
    }
  }
}
```

### 3. SSE Connection Management

```javascript
// ✅ Good: Cleanup on unmount
useEffect(() => {
  let reader;
  
  const streamChat = async () => {
    const response = await fetch(/* ... */);
    reader = response.body.getReader();
    // ... stream processing
  };
  
  streamChat();
  
  return () => {
    // Cancel stream on unmount
    reader?.cancel();
  };
}, []);
```

### 4. Device Fingerprinting

```javascript
// ✅ Good: Cache fingerprint
let cachedFingerprint = null;

async function getDeviceFingerprint() {
  if (cachedFingerprint) return cachedFingerprint;
  
  cachedFingerprint = await generateFingerprint();
  return cachedFingerprint;
}

// Include in requests
headers: {
  'X-Device-Fingerprint': await getDeviceFingerprint()
}
```

### 5. Trace Visualization

```javascript
// ✅ Good: Render steps in sequence
function TraceTimeline({ steps }) {
  return (
    <div className="timeline">
      {steps.sort((a, b) => a.sequence_order - b.sequence_order).map(step => (
        <div key={step.id} className={`step step-${step.step_type}`}>
          <h4>{step.step_name || step.step_type}</h4>
          <span>{step.latency_ms}ms</span>
          {step.output_payload && (
            <pre>{JSON.stringify(step.output_payload, null, 2)}</pre>
          )}
        </div>
      ))}
    </div>
  );
}
```

### 6. Cost Tracking

```javascript
// ✅ Good: Display costs clearly
function formatCost(cost) {
  const cents = parseFloat(cost) * 100;
  return cents < 0.01 
    ? `$${parseFloat(cost).toFixed(6)}` 
    : `$${parseFloat(cost).toFixed(4)}`;
}

// Usage
<span>Cost: {formatCost(trace.total_cost)}</span>
```

### 7. Optimistic UI Updates

```javascript
// ✅ Good: Update UI immediately for better UX
async function sendMessage(message) {
  // Add optimistic message
  setMessages(prev => [...prev, {
    id: 'temp-' + Date.now(),
    content: message,
    isPending: true
  }]);
  
  try {
    await client.streamChat(message, (data) => {
      // Replace with real response
      if (data.type === 'complete') {
        setMessages(prev => prev.filter(m => !m.isPending));
      }
    });
  } catch (error) {
    // Remove optimistic message on error
    setMessages(prev => prev.filter(m => !m.isPending));
  }
}
```

---

## 🔗 Additional Resources

- **OpenAPI Spec**: `GET /openapi.json`
- **Interactive Docs**: `GET /docs` (Swagger UI)
- **Database Schema**: [docs/DbSchema.md](./DbSchema.md)
- **User Flow**: [docs/UserFlow.md](./UserFlow.md)
- **README**: [README.md](../README.md)

---

## 📞 Support

For issues or questions:
- Check the interactive API docs at `/docs`
- Review the database schema in `docs/DbSchema.md`
- See user flow diagrams in `docs/UserFlow.md`

---

**Built with transparency and observability in mind** 🔍
