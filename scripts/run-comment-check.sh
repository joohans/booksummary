#!/bin/bash
# 매일 구독자 댓글 점검 (crontab 등록용)
# 미답변 댓글 목록을 data/comment_check_latest.txt 에 기록한다.
# 답글 문안은 판단이 필요하므로 게시는 하지 않는다 —
# 세션에서 "댓글 점검"이라고 하면 이 리포트를 근거로 답글을 작성/게시한다.
set -u

PROJ="/home/jsong/dev/jsong1230-github/booksummary"
PY="$PROJ/.venv/bin/python"
OUT="$PROJ/data/comment_check_latest.txt"
LOG="/tmp/booksummary-comment-check.log"

cd "$PROJ" || exit 1

{
  echo "# 구독자 댓글 점검 — $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo
  if ! "$PY" scripts/check_new_comments.py 2>&1; then
    echo "(점검 실패 — 위 오류 확인)"
  fi
} > "$OUT.tmp" 2>&1

mv "$OUT.tmp" "$OUT"

pending=$(grep -oP '미답변 댓글 \K[0-9]+' "$OUT" | head -1)
: "${pending:=0}"
echo "$(date '+%F %T') pending=${pending}" >> "$LOG"

# 대기 건이 있으면 종료코드로 표시 (cron 로그에서 눈에 띄게)
[ "$pending" -gt 0 ] && echo "미답변 ${pending}건 — $OUT 확인"
exit 0
