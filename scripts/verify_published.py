#!/usr/bin/env python3
"""예약 영상이 정상 공개됐는지 점검한다.

왜 필요한가 (2026-09-08 사고):
  새 선정 기준 8편이 **훅·제목·저자가 없는 배경 그림만** 썸네일로 올라간 채 공개돼 있었다.
  API 응답에 `maxres` 키가 있어서 "커스텀 썸네일 있음"으로 통과했기 때문이다.
  → **실제 이미지를 받아 텍스트 오버레이 유무까지** 검사한다.

사용:
    .venv/bin/python scripts/verify_published.py --video-id dqc8CnTIEbc
    .venv/bin/python scripts/verify_published.py --today     # 오늘 공개 예정분 전부
"""
import argparse
import io
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
KST = timezone(timedelta(hours=9))
PLAYLIST_KO = "PLrZ4eky3zPhJkKccHEIMN2bQPNPzFPzxT"  # [KOR] 책 요약 - 전체 모음


def yt_client():
    creds = Credentials.from_authorized_user_file(str(ROOT / "secrets/credentials.json"))
    return build("youtube", "v3", credentials=creds)


def has_text_overlay(url: str) -> tuple[bool, str]:
    """썸네일에 텍스트 오버레이가 있는지 판정한다.

    ⚠️ **우리 파이프라인(`thumbnail_generator.overlay_text`)이 만든 썸네일에만 유효하다.**
    그 함수는 항상 노란 테두리 프레임을 그리므로, 배경만 올라간 것과 확실히 갈린다
    (실측: 텍스트 없음 0% / 있음 70~75%).

    ⛔ **과거 영상에 적용하지 말 것.** 2026-09-11 에 채널 460편 전수 점검을 시도했다가
    두 번 연속 오탐을 냈다:
      1) 노란 테두리 기준 → Gems 시대의 **파란 프레임** 35편이 전부 "누락"으로 잡혔다
      2) '상단의 흰 글씨' 기준으로 바꿔도 → 빨강·노랑 글씨이거나 중앙·하단 배치인
         7편(종의 기원·목민심서·금병매·이반 일리치…)이 또 걸렸다
    채널의 썸네일 스타일이 시기마다 달라 **자동 전수 검사는 성립하지 않는다.**
    `--today` 로 갓 만든 편만 보는 용도로 쓴다.
    """
    try:
        from PIL import Image
        with urllib.request.urlopen(url, timeout=30) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGB")
    except Exception as e:  # noqa: BLE001
        return False, f"이미지 확인 실패: {str(e)[:50]}"

    w, h = im.size
    px = im.load()

    def yellowish(p) -> bool:
        r, g, b = p
        return r > 190 and g > 160 and b < 120

    band = max(2, min(w, h) // 120)          # 테두리 두께 추정
    pts, hit = 0, 0
    for x in range(0, w, max(1, w // 200)):   # 위/아래 가장자리
        for y in list(range(band)) + list(range(h - band, h)):
            pts += 1
            hit += yellowish(px[x, y])
    for y in range(0, h, max(1, h // 200)):   # 좌/우 가장자리
        for x in list(range(band)) + list(range(w - band, w)):
            pts += 1
            hit += yellowish(px[x, y])
    ratio = hit / max(pts, 1)
    return ratio > 0.5, f"현행 템플릿 테두리 {ratio*100:.0f}%"


def check(yt, vid: str) -> dict:
    r = yt.videos().list(part="snippet,status,statistics", id=vid).execute()["items"]
    if not r:
        return {"id": vid, "ok": False, "issues": ["영상을 찾을 수 없다"]}
    v = r[0]
    sn, st = v["snippet"], v["status"]
    issues, notes = [], []

    # 1) 공개 상태
    if st["privacyStatus"] != "public":
        pa = st.get("publishAt")
        when = ""
        if pa:
            when = f" (예약 {datetime.fromisoformat(pa.replace('Z','+00:00')).astimezone(KST):%m/%d %H:%M})"
        issues.append(f"아직 공개 아님: {st['privacyStatus']}{when}")
    else:
        pub = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00")).astimezone(KST)
        notes.append(f"공개 {pub:%m/%d %a %H:%M} KST")

    # 2) 썸네일 — 키 존재만으로는 부족하다
    th = sn.get("thumbnails", {})
    if "maxres" not in th and "standard" not in th:
        issues.append("커스텀 썸네일 없음")
    else:
        url = (th.get("maxres") or th.get("standard"))["url"]
        ok, why = has_text_overlay(url)
        if ok:
            notes.append(f"썸네일 텍스트 있음 ({why})")
        else:
            issues.append(f"⚠️ 썸네일에 텍스트 오버레이가 없다 ({why}) — 배경만 올라간 것일 수 있다")

    # 3) 태그
    tags = sn.get("tags", [])
    if len(tags) < 20:
        issues.append(f"태그 {len(tags)}개 (큐레이션 26개 기대)")
    else:
        notes.append(f"태그 {len(tags)}개")

    # 4) 언어
    if sn.get("defaultLanguage") != "ko":
        issues.append(f"defaultLanguage={sn.get('defaultLanguage')}")

    # 5) 재생목록
    try:
        ids, tok = [], None
        while True:
            pr = yt.playlistItems().list(part="contentDetails", playlistId=PLAYLIST_KO,
                                         maxResults=50, pageToken=tok).execute()
            ids += [i["contentDetails"]["videoId"] for i in pr["items"]]
            tok = pr.get("nextPageToken")
            if not tok:
                break
        if vid in ids:
            notes.append("재생목록 포함")
        else:
            issues.append("재생목록에 없음")
    except Exception as e:  # noqa: BLE001
        notes.append(f"재생목록 확인 실패({str(e)[:40]})")

    # 6) 고정 댓글 — 공개 후에만 달 수 있다
    if st["privacyStatus"] == "public":
        try:
            ct = yt.commentThreads().list(part="snippet", videoId=vid, maxResults=20).execute()
            mine = [t for t in ct.get("items", [])
                    if t["snippet"]["topLevelComment"]["snippet"].get("authorChannelId", {}).get("value")
                    == sn.get("channelId")]
            notes.append(f"채널 댓글 {len(mine)}건" if mine else "채널 댓글 없음 (16:10 cron 이 처리)")
        except Exception as e:  # noqa: BLE001
            notes.append(f"댓글 확인 실패({str(e)[:40]})")

    s = v.get("statistics", {})
    notes.append(f"조회 {s.get('viewCount','—')} · 좋아요 {s.get('likeCount','—')}")
    return {"id": vid, "title": sn["title"], "ok": not issues, "issues": issues, "notes": notes}


def todays_scheduled(yt) -> list[str]:
    """오늘(KST) 공개 예정이거나 오늘 공개된 영상 id."""
    ch = yt.channels().list(part="contentDetails", mine=True).execute()
    pl = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=pl,
                                    maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break
    today = datetime.now(KST).date()
    out = []
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="status,snippet", id=",".join(ids[i:i + 50])).execute()["items"]:
            when = v["status"].get("publishAt") or v["snippet"].get("publishedAt")
            if when and datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(KST).date() == today:
                out.append(v["id"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video-id", nargs="*", default=[])
    ap.add_argument("--today", action="store_true", help="오늘 공개(예정)분 전부")
    args = ap.parse_args()

    yt = yt_client()
    vids = list(args.video_id)
    if args.today or not vids:
        vids += todays_scheduled(yt)
    if not vids:
        print("점검 대상 없음 (오늘 공개 예정분이 없다)")
        return 0

    bad = 0
    print(f"공개 점검 — {datetime.now(KST):%Y-%m-%d %a %H:%M} KST\n")
    for vid in dict.fromkeys(vids):
        r = check(yt, vid)
        mark = "✅" if r["ok"] else "❌"
        print(f"{mark} {r.get('title','?')[:56]}  ({vid})")
        for n in r.get("notes", []):
            print(f"     · {n}")
        for i in r.get("issues", []):
            print(f"     ⚠️ {i}")
            bad += 1
        print()
    print("이상 없음" if not bad else f"조치 필요 {bad}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
