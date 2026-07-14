#!/usr/bin/env bash
# Image entrypoint: run `ollama serve` on 11434 plus a tiny nginx reverse proxy
# on $PORT that adds the /ping health route Runpod *load-balancing* serverless
# endpoints require, forwarding everything else to Ollama.
#
#   - LB serverless endpoint: Runpod hits $PORT (default 80) — /ping returns 200,
#     /api/* is proxied to Ollama (so https://<id>.api.runpod.ai/api/chat works).
#   - GPU Pod: expose 11434 directly and hit Ollama as usual; the proxy just sits
#     idle on $PORT. One image serves both paths.
#
# NOTE (unverified): the exact $PORT vs PORT_HEALTH wiring for LB endpoints should
# be confirmed on first deploy; this proxies BOTH /ping and the API on one port,
# which is the safe superset.
set -euo pipefail

PORT="${PORT:-80}"

# Render the nginx site: /ping -> 200, everything else -> Ollama (streaming-safe).
cat > /etc/nginx/conf.d/ollama-lb.conf <<EOF
server {
    listen ${PORT};
    location = /ping {
        access_log off;
        return 200 'ok';
    }
    location / {
        proxy_pass http://127.0.0.1:11434;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_buffering off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
EOF

# Drop the stock default site so it doesn't fight for port 80.
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# Start Ollama and wait until it accepts connections before serving traffic.
ollama serve &
OLLAMA_PID=$!
for _ in $(seq 1 60); do
    if (exec 3<>/dev/tcp/127.0.0.1/11434) 2>/dev/null; then exec 3>&- 3<&-; break; fi
    sleep 1
done

# If Ollama exits, bring the container down too (otherwise nginx would linger).
( wait "$OLLAMA_PID"; echo "ollama serve exited" >&2; kill -TERM 1 ) &

exec nginx -g 'daemon off;'
