FROM gotenberg/gotenberg:8

LABEL org.opencontainers.image.title="aio_gotenburg_ngnix" \
      org.opencontainers.image.description="All-in-one Gotenberg + Nginx + Flask PDF service" \
      org.opencontainers.image.source="https://github.com/devhako/aio_gotenburg_ngnix" \
      org.opencontainers.image.licenses="MIT"

USER root

COPY requirements.txt requirements.txt

ENV API_BIND_IP="127.0.0.1" \
    API_PORT="3000" \
    CHROMIUM_DENY_PRIVATE_IPS="true" \
    API_DOWNLOAD_FROM_DENY_PRIVATE_IPS="true" \
    PYTHONDONTWRITEBYTECODE="1" \
    PYTHONUNBUFFERED="1"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gettext-base \
        nginx \
        python3 \
        python3-venv \
        tini \
        util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/pdf-link/venv \
    && /opt/pdf-link/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && mkdir -p /opt/pdf-link /data/files /etc/nginx/templates \
    && chown -R www-data:www-data /data/files

COPY app.py /opt/pdf-link/app.py
COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template
COPY start-pdf-link /usr/local/bin/start-pdf-link

RUN chmod 0755 /usr/local/bin/start-pdf-link

VOLUME ["/data/files"]
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8080/healthz >/dev/null || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/start-pdf-link"]
