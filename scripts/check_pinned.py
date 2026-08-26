#!/usr/bin/env python3
"""고정 댓글 여부 확인 + 좋아요·답글 추적 (고정 효과 측정용).

**왜 브라우저를 쓰나**: YouTube Data API v3 에는 고정(pin) 관련 필드가 없다
(discovery 문서 전수 확인, 2026-08-25). 고정 여부는 워치 페이지에서만 보인다.
다행히 고정 댓글은 로그아웃 상태에서도 맨 위에 "…님이 고정함" 배지와 함께 노출된다.

대상과 기준선은 data/pin_experiment_baseline.json 을 읽는다.
좋아요·답글 수는 Data API 로 가져온다(1 unit/편).

사용: DISPLAY=:99 python3 scripts/check_pinned.py
"""
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "data" / "pin_experiment_baseline.json"


def comment_stats(video_ids):
    """댓글 좋아요·답글 수 (Data API). 실패해도 None 으로 진행한다."""
    try:
        from dotenv import load_dotenv
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        load_dotenv(ROOT / ".env")
        creds = Credentials(
            token=None,
            refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("YOUTUBE_CLIENT_ID"),
            client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
        )
        creds.refresh(Request())
        yt = build("youtube", "v3", credentials=creds)
        mine = yt.channels().list(part="id", mine=True).execute()["items"][0]["id"]
        out = {}
        for vid in video_ids:
            try:
                th = yt.commentThreads().list(
                    part="snippet", videoId=vid, maxResults=20
                ).execute().get("items", [])
            except Exception:
                continue
            for t in th:
                s = t["snippet"]["topLevelComment"]["snippet"]
                if s.get("authorChannelId", {}).get("value") == mine:
                    out[vid] = (int(s.get("likeCount", 0)), t["snippet"].get("totalReplyCount", 0))
                    break
        return out
    except Exception as e:  # noqa: BLE001
        print(f"(댓글 통계 조회 실패: {str(e)[:60]})", file=sys.stderr)
        return {}


async def check_pins(videos):
    from playwright.async_api import async_playwright

    result = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        for v in videos:
            vid = v["video_id"]
            pg = await b.new_page(viewport={"width": 1280, "height": 1000})
            try:
                await pg.goto(
                    f"https://www.youtube.com/watch?v={vid}",
                    wait_until="domcontentloaded", timeout=60000,
                )
                await pg.wait_for_timeout(4000)
                for _ in range(5):  # 댓글은 스크롤해야 렌더된다
                    await pg.mouse.wheel(0, 800)
                    await pg.wait_for_timeout(1000)
                await pg.wait_for_selector("ytd-comment-thread-renderer", timeout=25000)
                first = pg.locator("ytd-comment-thread-renderer").first
                # ⚠️ 배지 요소(#pinned-comment-badge)는 고정되지 않은 댓글에도 DOM 에 존재한다
                # (숨겨진 채로). count() 로 세면 전부 고정으로 오판한다 — 2026-08-27 실측.
                # 실제 신호는 렌더된 텍스트의 "…님이 고정함" / "Pinned by" 뿐이다.
                text = await first.inner_text()
                result[vid] = ("님이 고정함" in text) or ("Pinned by" in text)
            except Exception as e:  # noqa: BLE001
                print(f"   {vid} 확인 실패: {str(e)[:60]}", file=sys.stderr)
                result[vid] = None
            await pg.close()
        await b.close()
    return result


def main():
    data = json.loads(BASELINE.read_text())
    videos = data["videos"]
    pins = asyncio.run(check_pins(videos))
    stats = comment_stats([v["video_id"] for v in videos])

    print(f"기준선 기록일: {data['recorded']}  (고정일: {data.get('pinned_at', '미기록')})\n")
    print(f"{'고정':<4} {'조회':>6} {'좋아요':>12} {'답글':>10}  영상")
    for v in sorted(videos, key=lambda x: -x["views"]):
        vid = v["video_id"]
        mark = {True: "📌", False: "—", None: "?"}[pins.get(vid)]
        like, rep = stats.get(vid, (None, None))
        dl = f"{v['comment_likes']}→{like}" if like is not None else "—"
        dr = f"{v['comment_replies']}→{rep}" if rep is not None else "—"
        print(f"{mark:<4} {v['views']:>6,} {dl:>12} {dr:>10}  {v['title'][:44]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
