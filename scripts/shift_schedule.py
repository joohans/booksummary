#!/usr/bin/env python3
"""예약 공개일 일괄 이동 — 근접 슬롯에 새 편을 끼워 넣을 때 쓴다.

사용자 지시 방식(4회째): 새 편을 원하는 날짜에 넣고,
그 날짜 이후의 예약 편들을 전부 같은 일수만큼 뒤로 민다.
간격 패턴은 전부 같은 값을 더하므로 그대로 유지된다.

    # 미리보기 (기본)
    .venv/bin/python scripts/shift_schedule.py --from 2026-10-02 --days 3
    # 실제 적용
    .venv/bin/python scripts/shift_schedule.py --from 2026-10-02 --days 3 --apply
"""
import argparse
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

KST = timezone(timedelta(hours=9))
STATUS_KEYS = ("privacyStatus", "embeddable", "license", "publicStatsViewable", "selfDeclaredMadeForKids")


def scheduled_videos(yt):
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
    out = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="status,snippet", id=",".join(ids[i:i + 50])).execute()
        for v in r["items"]:
            pa = v["status"].get("publishAt")
            if pa:
                out.append((pa, v["snippet"]["title"], v["id"], v))
    out.sort()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", required=True, help="이 날짜(KST) 이후를 민다 (YYYY-MM-DD, 경계 포함)")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--exclude", nargs="*", default=[], help="제외할 videoId (새로 넣은 편)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    boundary = datetime.strptime(args.frm, "%Y-%m-%d").replace(tzinfo=KST)
    creds = Credentials.from_authorized_user_file("secrets/credentials.json")
    yt = build("youtube", "v3", credentials=creds)

    targets = []
    for pa, title, vid, v in scheduled_videos(yt):
        if vid in args.exclude:
            continue
        cur = datetime.fromisoformat(pa.replace("Z", "+00:00")).astimezone(KST)
        if cur >= boundary:
            targets.append((cur, cur + timedelta(days=args.days), title, vid, v))

    print(f"대상 {len(targets)}편 (+{args.days}일)\n")
    for cur, new, title, vid, _ in targets:
        print(f"  {cur:%m/%d %a} → {new:%m/%d %a}  {title[:48]}  {vid}")

    if not args.apply:
        print("\n미리보기입니다. 실제 적용하려면 --apply 를 붙이세요.")
        return

    # 뒤에서부터 밀어야 날짜 충돌이 생기지 않는다
    print()
    for cur, new, title, vid, v in reversed(targets):
        # 빠진 필드는 기본값으로 덮어쓰이므로(embeddable·publicStatsViewable 이 False 가 됐다)
        # 기존 status 를 전부 실어 보낸다
        status = {k: v["status"][k] for k in STATUS_KEYS if k in v["status"]}
        status["publishAt"] = new.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        body = {"id": vid, "status": status}
        yt.videos().update(part="status", body=body).execute()
        print(f"  ✅ {new:%m/%d %a} {title[:42]}")
    print(f"\n{len(targets)}편 이동 완료")


if __name__ == "__main__":
    main()
