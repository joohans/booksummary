#!/usr/bin/env python3
"""Shorts 스프린트 업로드 — 비공개 + 예약 공개, 전용 재생목록, 본편 기준값 저장.

사용법:
  upload_shorts.py data/shorts/sprint1.json --start 2026-10-05 --per-day 2 [--dry-run]

- 하루 per-day 편씩, 18:00 KST(09:00Z)부터 30분 간격으로 예약
- 결과: data/shorts/<sprint>_uploads.json (영상 ID·공개 시각·본편 기준 조회수)
- 재생목록 「1분 줄거리 (Shorts)」 가 없으면 만든다
"""
import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
PLAYLIST_TITLE = "1분 줄거리 (Shorts)"


def retry(fn, n=5):
    for t in range(n):
        try:
            return fn()
        except HttpError as e:
            if e.resp.status in (409, 500, 503) and t < n - 1:
                time.sleep(3 * (t + 1))
                continue
            raise


def playlist_id(yt):
    tok = None
    while True:
        r = yt.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=tok).execute()
        for p in r["items"]:
            if p["snippet"]["title"] == PLAYLIST_TITLE:
                return p["id"]
        tok = r.get("nextPageToken")
        if not tok:
            break
    body = {"snippet": {"title": PLAYLIST_TITLE, "defaultLanguage": "ko",
                        "description": "책 한 권의 줄거리를 결말까지 1분으로. 전체 해설은 각 영상 설명란의 본편 링크에서."},
            "status": {"privacyStatus": "public"}}
    return yt.playlists().insert(part="snippet,status", body=body).execute()["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--start", required=True)
    ap.add_argument("--per-day", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = json.loads((ROOT / a.config).read_text(encoding="utf-8"))
    out = ROOT / a.config.replace(".json", "_uploads.json")
    state = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"videos": {}}

    yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file(str(ROOT / "secrets" / "credentials.json")))
    start = dt.date.fromisoformat(a.start)
    plan = []
    for k, s in enumerate(cfg["shorts"]):
        day = start + dt.timedelta(days=k // a.per_day)
        at = dt.datetime(day.year, day.month, day.day, 9, 30 * (k % a.per_day), tzinfo=dt.timezone.utc)
        plan.append((s, at.strftime("%Y-%m-%dT%H:%M:%SZ")))
    for s, at in plan:
        print(f"  {at}  {s['book']}")
    if a.dry_run:
        return

    # 본편 기준값(업로드 전 누적 조회수)
    if "baseline" not in state:
        ids = [s["long_video"] for s in cfg["shorts"]]
        vs = yt.videos().list(part="statistics", id=",".join(ids)).execute()["items"]
        state["baseline"] = {"date": dt.date.today().isoformat(),
                             "long_views": {v["id"]: int(v["statistics"].get("viewCount", 0)) for v in vs}}
        out.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    pl = playlist_id(yt)
    state["playlist"] = pl
    for s, at in plan:
        if s["slug"] in state["videos"]:
            print(f"  건너뜀(이미 업로드): {s['book']}")
            continue
        meta = json.loads((ROOT / "output" / "shorts" / f"{s['slug']}.metadata.json").read_text(encoding="utf-8"))
        body = {"snippet": {"title": meta["title"], "description": meta["description"], "tags": meta["tags"],
                            "categoryId": "22", "defaultLanguage": "ko", "defaultAudioLanguage": "ko"},
                "status": {"privacyStatus": "private", "publishAt": at, "selfDeclaredMadeForKids": False}}
        media = MediaFileUpload(str(ROOT / meta["video_path"]), mimetype="video/mp4", resumable=True)
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
        vid = resp["id"]
        thumb = ROOT / "output" / "shorts" / f"{s['slug']}_thumb.jpg"
        if thumb.exists():  # 자동 썸네일은 아무 프레임이나 고른다 → 제목이 큰 커스텀 썸네일
            retry(lambda: yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb))).execute())
        retry(lambda: yt.playlistItems().insert(part="snippet", body={"snippet": {
            "playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute())
        state["videos"][s["slug"]] = {"id": vid, "book": s["book"], "publish_at": at, "long_video": s["long_video"]}
        out.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ {s['book']}: https://youtube.com/shorts/{vid}  ({at})")
    print(f"재생목록: https://www.youtube.com/playlist?list={pl}")


if __name__ == "__main__":
    sys.exit(main())
