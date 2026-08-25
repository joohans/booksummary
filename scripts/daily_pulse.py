#!/usr/bin/env python3
"""매일 채널 반응 점검 — 조회수·유입·검색어·최근 공개 편 성과를 한 장으로 뽑는다.

선정 기준을 "검색 수요 × 한국어 공급"으로 바꾼 뒤(2026-08-24) 판정 근거가 되는 지표만 모은다.
출력은 data/daily_pulse_latest.md. cron 은 scripts/run-daily-pulse.sh 가 돈다.

주의: YouTube Analytics 는 2~3일 지연된다. 어제 데이터가 없는 것은 정상이다.
"""
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
# 선정 기준 실험 — 경쟁 낮음 3편 vs 옛 기준(경쟁 높음) 3편
EXPERIMENT = {
    "ntig_j4dKHo": "생명이란 무엇인가 (경쟁 1,608)",
    "uz4SWTTK73Q": "화씨 451 (경쟁 1,423)",
    "kxckIkN0_Cc": "부분과 전체 (경쟁 1,962)",
}
CONTROL = {
    "j0wh-_pP_20": "1984 (경쟁 89,963)",
    "nHs48G5txbk": "죄와 벌 (경쟁 98,243)",
    "_GIZV21TV1I": "동물농장 (경쟁 344,595)",
}


def clients():
    load_dotenv(ROOT / ".env")
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("YOUTUBE_CLIENT_ID"),
        client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds), build(
        "youtubeAnalytics", "v2", credentials=creds
    )


def q(ya, **kw):
    """Analytics 조회. 실패해도 리포트 전체를 죽이지 않는다."""
    try:
        return ya.reports().query(ids="channel==MINE", **kw).execute().get("rows", [])
    except Exception as e:  # noqa: BLE001
        print(f"  (조회 실패: {e})", file=sys.stderr)
        return []


def channel_daily(ya, out, today):
    start = today - timedelta(days=14)
    rows = q(
        ya,
        startDate=start.isoformat(),
        endDate=today.isoformat(),
        metrics="views,estimatedMinutesWatched,averageViewPercentage,subscribersGained,subscribersLost",
        dimensions="day",
    )
    rows.sort()
    out.append("## 일별 채널 지표 (최근 2주)\n")
    if not rows:
        out.append("데이터 없음\n")
        return
    out.append("| 날짜 | 조회 | 시청(분) | 평균 시청률 | 구독 +/- |")
    out.append("|---|---:|---:|---:|---:|")
    for d, v, m, p, sg, sl in rows[-14:]:
        out.append(f"| {d} | {v:,} | {m:,} | {p:.1f}% | +{sg}/-{sl} |")
    half = len(rows) // 2
    prev, cur = rows[:half], rows[half:]
    pv, cv = sum(r[1] for r in prev), sum(r[1] for r in cur)
    delta = f"{(cv - pv) / pv * 100:+.0f}%" if pv else "—"
    out.append(f"\n최근 {len(cur)}일 {cv:,}회 vs 직전 {len(prev)}일 {pv:,}회 → **{delta}**\n")


def traffic(ya, out, today):
    start = today - timedelta(days=7)
    rows = q(
        ya,
        startDate=start.isoformat(),
        endDate=today.isoformat(),
        metrics="views",
        dimensions="insightTrafficSourceType",
        sort="-views",
    )
    total = sum(r[1] for r in rows) or 1
    out.append("## 유입 경로 (최근 7일)\n")
    for name, v in rows[:6]:
        out.append(f"- {name}: {v:,} ({v / total * 100:.0f}%)")
    out.append("")


def search_terms(ya, out, today, days, label):
    start = today - timedelta(days=days)
    rows = q(
        ya,
        startDate=start.isoformat(),
        endDate=today.isoformat(),
        metrics="views",
        dimensions="insightTrafficSourceDetail",
        filters="insightTrafficSourceType==YT_SEARCH",
        sort="-views",
        maxResults=15,
    )
    out.append(f"## 유입 검색어 ({label})\n")
    if not rows:
        out.append("데이터 없음\n")
        return
    for term, v in rows:
        out.append(f"- {v:>4,}  {term}")
    out.append("")


def tracked(ya, yt, out, today):
    """실험 편 / 대조군 추적 — 공개된 것만 나온다."""
    ids = {**EXPERIMENT, **CONTROL}
    meta = {}
    for item in yt.videos().list(part="status,statistics,snippet", id=",".join(ids)).execute()["items"]:
        meta[item["id"]] = item

    out.append("## 선정 기준 실험 추적\n")
    out.append("| 편 | 상태 | 조회 | 좋아요 | 댓글 | 평균 시청률 |")
    out.append("|---|---|---:|---:|---:|---:|")
    for group, label in ((EXPERIMENT, "실험"), (CONTROL, "대조")):
        for vid, name in group.items():
            m = meta.get(vid)
            if not m:
                out.append(f"| [{label}] {name} | (없음) | — | — | — | — |")
                continue
            st = m["status"]
            if st["privacyStatus"] != "public":
                when = (st.get("publishAt") or "")[:10]
                out.append(f"| [{label}] {name} | 예약 {when} | — | — | — | — |")
                continue
            s = m["statistics"]
            rows = q(
                ya,
                startDate=m["snippet"]["publishedAt"][:10],
                endDate=today.isoformat(),
                metrics="averageViewPercentage",
                filters=f"video=={vid}",
            )
            avp = f"{rows[0][0]:.1f}%" if rows else "—"
            out.append(
                f"| [{label}] {name} | 공개 | {int(s.get('viewCount', 0)):,} | "
                f"{int(s.get('likeCount', 0)):,} | {int(s.get('commentCount', 0)):,} | {avp} |"
            )
    out.append("")


def actions(yt, out, today):
    """오늘 처리할 수 있는 것 — 공개 전환 직후의 고정 댓글이 대표적이다."""
    out.append("## 오늘의 액션\n")
    todo = []

    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while len(ids) < 60:
        r = yt.playlistItems().list(
            part="contentDetails", playlistId=up, maxResults=50, pageToken=tok
        ).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break

    cutoff = (today - timedelta(days=10)).isoformat()
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="snippet,status", id=",".join(ids[i : i + 50])).execute()["items"]:
            if v["status"]["privacyStatus"] != "public":
                continue
            if v["snippet"]["publishedAt"][:10] < cutoff:
                continue
            try:
                th = yt.commentThreads().list(
                    part="snippet", videoId=v["id"], maxResults=20
                ).execute()["items"]
            except Exception:  # noqa: BLE001
                continue
            mine_ch = ch["id"]
            has_own = any(
                t["snippet"]["topLevelComment"]["snippet"].get("authorChannelId", {}).get("value") == mine_ch
                for t in th
            )
            if not has_own:
                todo.append(f"- **고정 댓글 없음** — {v['snippet']['title'][:50]} (`{v['id']}`)")

    # "미답변 댓글 3건" 처럼 건수가 붙은 줄만 조치 대상이다.
    # "미답변 댓글 없음 ✅" 을 조치 필요로 세던 버그가 있었다 (2026-08-25).
    pending = ROOT / "data" / "comment_check_latest.txt"
    if pending.exists():
        m = re.search(r"미답변 댓글\s+(\d+)\s*건", pending.read_text())
        if m and int(m.group(1)) > 0:
            todo.append(f"- 미답변 댓글 {m.group(1)}건 → `data/comment_check_latest.txt`")

    out.extend(todo or ["- 없음"])
    out.append("")


def main():
    today = date.today()
    yt, ya = clients()
    out = [
        f"# 채널 반응 점검 — {today.isoformat()}",
        "",
        "> Analytics 는 2~3일 지연된다. 최근 1~2일이 비어 있는 것은 정상.",
        "",
    ]
    channel_daily(ya, out, today)
    traffic(ya, out, today)
    search_terms(ya, out, today, 7, "최근 7일")
    search_terms(ya, out, today, 28, "최근 28일")
    tracked(ya, yt, out, today)
    actions(yt, out, today)

    dest = ROOT / "data" / "daily_pulse_latest.md"
    dest.write_text("\n".join(out) + "\n")
    print(f"저장: {dest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
