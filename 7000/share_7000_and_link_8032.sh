#!/data/data/com.termux/files/usr/bin/bash
set -u
ROOT7000="$(cd "$(dirname "$0")" && pwd)"
ROOT8032="$(dirname "$ROOT7000")"
LOG="${TMPDIR:-$HOME}/infini_cf_7000_$$.log"
rm -f "$LOG"

echo "กำลังสร้างลิงก์แชร์ 7000..."
cloudflared tunnel --protocol http2 --url http://127.0.0.1:7000 2>&1 | tee "$LOG" &
CFPID=$!

URL=""
for _ in $(seq 1 60); do
  URL=$(grep -Eo 'https://[-a-z0-9]+\.trycloudflare\.com' "$LOG" | tail -n 1 || true)
  [ -n "$URL" ] && break
  kill -0 "$CFPID" 2>/dev/null || break
  sleep 1
done

if [ -z "$URL" ]; then
  echo "❌ ยังสร้างลิงก์ 7000 ไม่สำเร็จ"
  kill "$CFPID" 2>/dev/null || true
  exit 1
fi

python "$ROOT8032/set_infini_public_links.py" --7000 "$URL"
echo "✅ ลิงก์แชร์ 7000: $URL"
echo "เปิดหน้านี้ค้างไว้"
wait "$CFPID"
