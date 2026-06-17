#!/usr/bin/env bash

API_URL="https://pdf.example.com/"
API_KEY="example-api-key"

# JSON body
curl -X POST "$API_URL/upload" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content": "# Hello\n\nThis is a **PDF** generated from markdown."}'

# Multipart form
curl -X POST "$API_URL/upload" \
  -H "X-API-Key: $API_KEY" \
  -F "content=# Hello

This is a **PDF** generated from markdown."

# Raw text body
curl -X POST "$API_URL/upload" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: text/plain" \
  --data-binary "# Hello

This is a **PDF** generated from markdown."
