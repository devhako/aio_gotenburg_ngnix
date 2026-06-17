#!/usr/bin/env bash

API_URL="https://pdf.example.com/"
API_KEY="example-api-key"

# --- Markdown (default mode) ---

# JSON body
curl -X POST "$API_URL/upload" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content": "# Hello\n\nThis is a **PDF** generated from markdown."}'

# JSON body with explicit mode
curl -X POST "$API_URL/upload" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"mode": "markdown", "content": "# Hello\n\nThis is a **PDF** generated from markdown."}'

# Multipart form
curl -X POST "$API_URL/upload" \
  -H "X-API-Key: $API_KEY" \
  -F "mode=markdown" \
  -F "content=# Hello

This is a **PDF** generated from markdown."

# Raw text body (defaults to markdown when Content-Type is not text/html)
curl -X POST "$API_URL/upload" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: text/plain" \
  --data-binary "# Hello

This is a **PDF** generated from markdown."

# --- HTML mode ---

# JSON body
curl -X POST "$API_URL/upload" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"mode": "html", "content": "<!doctype html><html><body><h1>Hello</h1><p>Generated from <strong>HTML</strong>.</p></body></html>"}'

# Multipart form
curl -X POST "$API_URL/upload" \
  -H "X-API-Key: $API_KEY" \
  -F "mode=html" \
  -F 'content=<!doctype html><html><body><h1>Hello</h1><p>Generated from <strong>HTML</strong>.</p></body></html>'

# Raw body with ?mode=html query param
curl -X POST "$API_URL/upload?mode=html" \
  -H "X-API-Key: $API_KEY" \
  --data-binary '<!doctype html><html><body><h1>Hello</h1></body></html>'
