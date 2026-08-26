#!/bin/bash
# 고정 댓글 따라잡기 (crontab 등록용, 매일 16:10 = 쿼터 리셋 10분 뒤)
#
# 하는 일: 공개 영상 중 우리 댓글이 없는 편에 제휴 링크 댓글을 단다.
#   - 쿼터가 떨어지면 스크립트가 스스로 중단하고, 다음 날 이어서 처리한다
#   - 예약(비공개) 영상은 사전 필터로 제외된다 → 공개 전환되면 자동으로 대상이 된다
# 전수 스캔 비용은 약 455 units (일일 10,000 중 4.5%).
set -u

PROJ="/home/jsong/dev/jsong1230-github/booksummary"
PY="$PROJ/.venv/bin/python"
LOG="/tmp/booksummary-pin-catchup.log"
RUN="$PROJ/logs/pin_catchup_last.log"

cd "$PROJ" || exit 1

"$PY" -u src/25_batch_add_pinned_comments.py --apply > "$RUN" 2>&1

added=$(grep -oP '추가: \K[0-9]+' "$RUN" | tail -1)
errors=$(grep -oP '오류: \K[0-9]+' "$RUN" | tail -1)
: "${added:=0}"; : "${errors:=0}"
quota=$(grep -c "quotaExceeded" "$RUN" || true)

echo "$(date '+%F %T') added=${added} errors=${errors} quota_hits=${quota}" >> "$LOG"
[ "$added" -gt 0 ] && echo "고정 댓글 ${added}편 추가 — $RUN"
[ "$quota" -gt 0 ] && echo "쿼터 소진으로 중단 — 내일 이어서 처리됩니다"

exit 0
