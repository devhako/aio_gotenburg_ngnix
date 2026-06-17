# aio-gotenberg-nginx

An all-in-one Docker image that bundles [Gotenberg](https://gotenberg.dev) (Chromium-based PDF conversion), a lightweight Flask/Gunicorn API, and Nginx into a single container — no orchestration required.

## Features

- **Markdown → PDF** — POST markdown content and receive a PDF rendered via headless Chromium
- **Serve** — PDFs are served publicly over HTTP and purged automatically after 24 hours
- **Secure by default** — API key auth on write endpoints, private IP deny rules, no directory listing, `server_tokens off`

## Quick start

```sh
docker run -d \
  -e PUBLIC_URL=https://pdf.example.com \
  -e API_KEY=your-secret-key \
  -p 8080:8080 \
  -v pdf-data:/data/files \
  ghcr.io/adjscent/aio-gotenburg-ngnix:latest
```

## Configuration

All settings are environment variables.

| Variable | Default | Description |
|---|---|---|
| `PUBLIC_URL` | **required** | Base URL where PDFs are served, e.g. `https://pdf.example.com` |
| `API_KEY` | **required** | Secret sent in the `X-API-Key` request header |
| `MAX_UPLOAD_MB` | `50` | Maximum size of incoming markdown content (MB) |
| `MAX_GENERATED_MB` | `100` | Maximum size of the generated PDF (MB) |
| `PURGE_AFTER_HOURS` | `24` | Hours before stored PDFs are deleted |
| `CLEANUP_INTERVAL_SECONDS` | `3600` | How often the cleanup job runs |
| `GOTENBERG_TIMEOUT_SECONDS` | `600` | Chromium conversion timeout |

```
PUBLIC_URL=https://pdf.example.com
API_KEY=you-should-change-this
MAX_UPLOAD_MB=50
MAX_GENERATED_MB=100
PURGE_AFTER_HOURS=24	
CLEANUP_INTERVAL_SECONDS=3600
GOTENBERG_TIMEOUT_SECONDS=600
```

## API

### Convert markdown to PDF

Accepts markdown as a raw body (`text/plain` or `text/markdown`), a JSON field, or a multipart field:

```sh
# raw body
curl -X POST https://pdf.example.com/upload \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: text/markdown" \
  --data-binary "# Hello\n\nThis is a **PDF**."

# JSON
curl -X POST https://pdf.example.com/upload \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"content": "# Hello\n\nThis is a **PDF**."}'

# multipart
curl -X POST https://pdf.example.com/upload \
  -H "X-API-Key: your-secret-key" \
  -F "content=# Hello"
```

Response `201`:

```json
{
  "id": "a3f...",
  "url": "https://pdf.example.com/files/a3f....pdf",
  "created_at": "2026-06-17T12:00:00+00:00",
  "expires_at": "2026-06-18T12:00:00+00:00",
  "expires_in_seconds": 86400
}
```

### Download a PDF

```
GET /files/<id>.pdf
```

No authentication required. Links expire after `PURGE_AFTER_HOURS` (default 24 hours).

## Architecture

```
Internet → Nginx :8080 ──┬── proxy → Gunicorn :9000 (Flask API)
                         │                 └── calls Gotenberg :3000 (Chromium)
                         └── static → /data/files (PDF downloads)
```

All processes run inside a single container supervised by [tini](https://github.com/krallin/tini). Gotenberg runs as the `gotenberg` user; the API and Nginx run as `www-data`. PDFs are stored under `/data/files` (mount a volume here for persistence).

## Building locally

```sh
docker build -t aio-gotenburg-nginx .
```

## License

[MIT](LICENSE)
