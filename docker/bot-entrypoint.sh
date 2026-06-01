#!/usr/bin/env bash
set -euo pipefail

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

if [ "$(id -u)" = "0" ]; then
    if ! getent group "$PGID" >/dev/null; then
        groupmod -g "$PGID" sentra
    fi

    usermod -u "$PUID" -g "$PGID" sentra

    mkdir -p /app/data /app/logs /home/sentra/.cache/huggingface
    chown -R "$PUID:$PGID" /app/data /app/logs /home/sentra/.cache

    exec gosu "$PUID:$PGID" "$@"
fi

exec "$@"
