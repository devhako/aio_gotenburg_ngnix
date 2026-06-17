import hmac
import os
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import requests
from flask import Flask, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

STORAGE_DIR = Path("/data/files")
PUBLIC_URL = os.environ["PUBLIC_URL"].rstrip("/")
API_KEY = os.environ["API_KEY"]
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_MB", "50")) * 1024 * 1024
MAX_GENERATED_BYTES = int(os.environ.get("MAX_GENERATED_MB", "100")) * 1024 * 1024
PURGE_AFTER_HOURS = int(os.environ.get("PURGE_AFTER_HOURS", "24"))
GOTENBERG_TIMEOUT_SECONDS = int(os.environ.get("GOTENBERG_TIMEOUT_SECONDS", "600"))
GOTENBERG_URL = os.environ.get(
    "GOTENBERG_URL",
    f"http://{os.environ.get('API_BIND_IP', '127.0.0.1')}:{os.environ.get('API_PORT', '3000')}",
)

# Gotenberg requires an HTML wrapper that references the markdown file via its template helper.
_MARKDOWN_WRAPPER = (
    '<!doctype html><html><head><meta charset="utf-8"></head>'
    '<body>{{ toHTML "content.md" }}</body></html>'
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES + (1024 * 1024)


def json_error(message: str, status: int):
    return jsonify({"error": message}), status


def require_api_key(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        supplied = request.headers.get("X-API-Key", "")
        if not supplied or not hmac.compare_digest(supplied, API_KEY):
            return json_error("unauthorized", 401)
        return handler(*args, **kwargs)

    return wrapped


def response_for_file(file_id: str):
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(hours=PURGE_AFTER_HOURS)
    return (
        jsonify(
            {
                "id": file_id,
                "url": f"{PUBLIC_URL}/files/{file_id}.pdf",
                "created_at": created_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "expires_in_seconds": PURGE_AFTER_HOURS * 3600,
            }
        ),
        201,
    )


def allocate_paths():
    file_id = uuid.uuid4().hex
    final_path = STORAGE_DIR / f"{file_id}.pdf"
    fd, temporary_path = tempfile.mkstemp(
        prefix=f".{file_id}-", suffix=".tmp", dir=STORAGE_DIR
    )
    return file_id, final_path, fd, Path(temporary_path)


def verify_pdf(path: Path):
    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValueError("file is not a valid PDF")


def save_stream(stream, maximum_bytes: int):
    file_id, final_path, fd, temporary_path = allocate_paths()
    total = 0

    try:
        try:
            fh = os.fdopen(fd, "wb")
        except OSError:
            os.close(fd)
            raise

        with fh as output:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > maximum_bytes:
                    raise RequestEntityTooLarge()
                output.write(chunk)

        if total == 0:
            raise ValueError("empty response from conversion service")

        verify_pdf(temporary_path)
        os.chmod(temporary_path, 0o640)
        os.replace(temporary_path, final_path)
        return file_id
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def read_content() -> tuple[str, str]:
    """Return (content, mode) where mode is 'markdown' or 'html'."""
    content_type = request.content_type or ""
    if "multipart/form-data" in content_type:
        mode = request.form.get("mode", "markdown").lower()
        return request.form.get("content", ""), mode
    if "application/json" in content_type:
        payload = request.get_json(silent=True) or {}
        mode = str(payload.get("mode", "markdown")).lower()
        return payload.get("content") or "", mode
    # Raw body: honour ?mode= query param, default to markdown
    mode = request.args.get("mode", "markdown").lower()
    return request.get_data(as_text=True), mode


@app.errorhandler(RequestEntityTooLarge)
def handle_too_large(_error):
    return json_error("content exceeds the configured size limit", 413)


@app.route("/upload", methods=["POST"])
@require_api_key
def upload():
    content, mode = read_content()
    if mode not in ("markdown", "html"):
        return json_error("mode must be 'markdown' or 'html'", 400)
    if not content or not content.strip():
        return json_error(f"{mode} content is required", 400)

    try:
        if mode == "markdown":
            upstream = requests.post(
                f"{GOTENBERG_URL}/forms/chromium/convert/markdown",
                files=[
                    ("files", ("index.html", _MARKDOWN_WRAPPER.encode(), "text/html")),
                    ("files", ("content.md", content.encode(), "text/markdown")),
                ],
                headers={"Gotenberg-Output-Filename": uuid.uuid4().hex},
                stream=True,
                timeout=(5, GOTENBERG_TIMEOUT_SECONDS),
            )
        else:
            upstream = requests.post(
                f"{GOTENBERG_URL}/forms/chromium/convert/html",
                files=[
                    ("files", ("index.html", content.encode(), "text/html")),
                ],
                headers={"Gotenberg-Output-Filename": uuid.uuid4().hex},
                stream=True,
                timeout=(5, GOTENBERG_TIMEOUT_SECONDS),
            )
    except requests.RequestException:
        return json_error("PDF conversion service is unavailable", 502)

    with upstream:
        if upstream.status_code != 200:
            return json_error("PDF conversion failed", 502)

        try:
            file_id = save_stream(upstream.raw, MAX_GENERATED_BYTES)
        except RequestEntityTooLarge:
            return json_error("generated PDF exceeds the configured size limit", 413)
        except ValueError:
            return json_error("conversion did not return a valid PDF", 502)

    return response_for_file(file_id)


@app.route("/healthz", methods=["GET"])
def healthz():
    try:
        response = requests.get(f"{GOTENBERG_URL}/health", timeout=2)
        if response.status_code != 200:
            return jsonify({"status": "unhealthy"}), 503
    except requests.RequestException:
        return jsonify({"status": "unhealthy"}), 503

    return jsonify({"status": "ok"}), 200
