#!/bin/bash
# 예약 영상 공개 직후 점검 — 18:05 KST (공개는 18:00)
cd "$HOME/dev/jsong1230-github/booksummary" || exit 1
OUT="data/publish_check_latest.md"
{
  echo "# 공개 점검 — $(TZ=Asia/Seoul date '+%Y-%m-%d %a %H:%M') KST"
  echo
  echo '```'
  .venv/bin/python scripts/verify_published.py --today 2>&1
  echo '```'
} > "$OUT"
echo "$(TZ=Asia/Seoul date '+%F %H:%M') 공개 점검 완료 → $OUT"
grep -q "조치 필요" "$OUT" && echo "⚠️ 조치 필요 — $OUT 확인"
