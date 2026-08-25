#!/bin/bash
# 매일 채널 반응 점검 (crontab 등록용)
# data/daily_pulse_latest.md 에 조회수·유입·검색어·실험 편 성과·오늘의 액션을 기록한다.
# 게시나 수정은 하지 않는다 — 판단이 필요한 조치는 세션에서 이 리포트를 근거로 실행한다.
set -u

PROJ="/home/jsong/dev/jsong1230-github/booksummary"
PY="$PROJ/.venv/bin/python"
OUT="$PROJ/data/daily_pulse_latest.md"
LOG="/tmp/booksummary-daily-pulse.log"

cd "$PROJ" || exit 1

if "$PY" scripts/daily_pulse.py >>"$LOG" 2>&1; then
  actions=$(sed -n '/^## 오늘의 액션/,$p' "$OUT" | grep -c '^- ' || true)
  # "- 없음" 한 줄만 있으면 액션 0건
  grep -q '^- 없음$' "$OUT" && actions=0
  echo "$(date '+%F %T') ok actions=${actions}" >> "$LOG"
  [ "$actions" -gt 0 ] && echo "조치 필요 ${actions}건 — $OUT 확인"
else
  echo "$(date '+%F %T') FAILED" >> "$LOG"
fi

exit 0
