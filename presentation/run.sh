#!/usr/bin/env bash
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PORT="${1:-8000}"
for try in "$PORT" 8080 8137 8765; do
    if ! (exec 3<>"/dev/tcp/127.0.0.1/$try") 2>/dev/null; then
        PORT="$try"; break
    fi
    exec 3>&- 2>/dev/null || true
done

python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null' EXIT INT TERM

sleep 1
URL="http://localhost:$PORT/index.html"
echo "Serving the deck at $URL"
echo "Press Ctrl-C to stop."
( xdg-open "$URL" >/dev/null 2>&1 || true ) &

wait "$SERVER_PID"
