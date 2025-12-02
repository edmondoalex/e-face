# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

# Dipendenze sistema + Caddy reverse proxy
RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl gnupg2 ca-certificates jq \
	&& mkdir -p /etc/apt/keyrings \
	&& curl -1sLf "https://dl.cloudsmith.io/public/caddy/stable/gpg.key" | gpg --dearmor -o /etc/apt/keyrings/caddy.gpg \
	&& curl -1sLf "https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt" | tee /etc/apt/sources.list.d/caddy-stable.list \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends caddy \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

# Installazione requirements backend
COPY e-face/backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Codice backend + frontend compilato
COPY e-face/backend/ ./backend/
COPY e-face/frontend_dist/ ./frontend_dist/

# Script di avvio custom
COPY run.sh /run.sh
RUN chmod +x /run.sh

ENV PYTHONUNBUFFERED=1 \
	APP_HOST=127.0.0.1 \
	APP_PORT=9000 \
	PUBLIC_HTTP_PORT=8000 \
	XDG_DATA_HOME=/data/caddy \
	XDG_CONFIG_HOME=/data/caddy/config

EXPOSE 8000 443

CMD ["/run.sh"]
