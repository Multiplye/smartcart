#!/usr/bin/env bash
#
# Expose the local Flask backend to the internet with a temporary
# public HTTPS URL, so a deployed frontend can reach it.
#
# WHY THIS IS NEEDED
#
#   The Vercel-hosted frontend and the Flask backend are on different
#   machines as far as the browser is concerned. The browser interprets
#   "127.0.0.1" as "the machine I am running on", so a visitor to the
#   deployed site would try to reach a Flask server on their own laptop
#   and fail.
#
#   This script gives the backend a real public URL. Paste that URL into
#   the frontend's VITE_API_URL and the deployed site can reach it.
#
# USAGE
#
#   1. Make sure Flask is running in another terminal:
#        cd backend && ./venv/Scripts/python.exe app.py
#
#   2. Run this script:
#        bash tools/start-tunnel.sh
#
#   3. Copy the https://....trycloudflare.com URL it prints.
#
#   4. Put it in smartcart/smartcart/.env as VITE_API_URL, or in the
#      Vercel dashboard under Settings -> Environment Variables, then
#      redeploy.
#
# LIMITATIONS - worth knowing before you rely on this
#
#   - The URL is RANDOM and changes every time you restart. That is a
#     property of Cloudflare "quick tunnels"; there is no free fixed
#     hostname. After every restart you must update VITE_API_URL and
#     redeploy, or the site goes back to failing.
#   - It only works while this script and Flask are both running, and
#     your laptop is awake and online.
#   - This is a demo tool, not a deployment. For a site that works for
#     anyone at any time, the backend needs a real host.

set -euo pipefail

# Work from the repository root, wherever this script is called from.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLOUDFLARED="$ROOT/tools/cloudflared.exe"
BACKEND="http://127.0.0.1:5000"

if [ ! -f "$CLOUDFLARED" ]; then
  echo "cloudflared.exe not found at $CLOUDFLARED"
  echo
  echo "Download it with:"
  echo "  curl -L -o tools/cloudflared.exe \\"
  echo "    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
  exit 1
fi

# Refuse to start if the backend is not up, because a tunnel pointing at
# nothing produces a confusing 502 in the browser rather than an obvious
# "backend is not running" message.
if ! curl -s -o /dev/null --noproxy '*' --max-time 5 "$BACKEND/api/products"; then
  echo "The Flask backend is not responding on $BACKEND"
  echo
  echo "Start it in another terminal first:"
  echo "  cd backend && ./venv/Scripts/python.exe app.py"
  exit 1
fi

echo "Backend is up. Opening a public tunnel..."
echo

"$CLOUDFLARED" tunnel --url "$BACKEND" --no-autoupdate
