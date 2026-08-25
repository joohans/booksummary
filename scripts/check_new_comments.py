#!/usr/bin/env python3
"""매일 점검용 — 답글이 없는 구독자 댓글만 뽑아서 보여준다.

답글 문안은 사람(또는 Claude)이 판단해야 하므로 이 스크립트는 '보고'만 한다.
실제 게시는 scripts/reply_to_comments.py 의 REPLIES 를 채우고 --apply.

사용:
  .venv/bin/python scripts/check_new_comments.py            # 미답변 전체
  .venv/bin/python scripts/check_new_comments.py --days 7    # 최근 7일만
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CHANNEL_ID = "UCxOcO_x_yW6sfg_FPUQVqYA"
OWNER = "@BeyondPage_Bi"
ROOT = Path(__file__).resolve().parent.parent
CREDS = ROOT / "secrets" / "credentials.json"


def load_ignored():
    """답하지 않기로 한 댓글 ID 집합. data/comment_ignore.txt 한 줄에 하나.

    `#` 이후는 주석이다. 답글 가치가 없다고 판단한 건(욕설·스팸)을 넣어 두면
    매일 리포트에 다시 뜨지 않는다.
    """
    f = ROOT / "data" / "comment_ignore.txt"
    if not f.exists():
        return set()
    out = set()
    for line in f.read_text(encoding="utf-8").splitlines():
        cid = line.split("#")[0].strip()
        if cid:
            out.add(cid)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, help="최근 N일 이내 댓글만")
    ap.add_argument("--show-ignored", action="store_true", help="무시 목록도 함께 표시")
    args = ap.parse_args()

    ignored = set() if args.show_ignored else load_ignored()

    yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file(str(CREDS)))

    items, tok = [], None
    while True:
        r = yt.commentThreads().list(
            part="snippet,replies", allThreadsRelatedToChannelId=CHANNEL_ID,
            maxResults=100, textFormat="plainText", pageToken=tok,
        ).execute()
        items += r.get("items", [])
        tok = r.get("nextPageToken")
        if not tok:
            break

    cutoff = None
    if args.days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    pending = []
    for it in items:
        sn = it["snippet"]["topLevelComment"]["snippet"]
        if sn["authorDisplayName"] == OWNER:
            continue
        published = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
        if cutoff and published < cutoff:
            continue
        if any(r["snippet"]["authorDisplayName"] == OWNER
               for r in it.get("replies", {}).get("comments", [])):
            continue
        if it["snippet"]["topLevelComment"]["id"] in ignored:
            continue
        pending.append({
            "cid": it["snippet"]["topLevelComment"]["id"],
            "vid": sn["videoId"],
            "author": sn["authorDisplayName"],
            "at": sn["publishedAt"][:10],
            "likes": sn.get("likeCount", 0),
            "text": sn["textDisplay"].replace("\n", " ").strip(),
        })

    if not pending:
        print("미답변 댓글 없음 ✅")
        return 0

    # 영상 제목 붙이기
    vids = sorted({p["vid"] for p in pending})
    titles = {}
    for i in range(0, len(vids), 50):
        for v in yt.videos().list(part="snippet", id=",".join(vids[i:i + 50])).execute()["items"]:
            titles[v["id"]] = v["snippet"]["title"]

    pending.sort(key=lambda p: p["at"], reverse=True)
    print(f"미답변 댓글 {len(pending)}건\n")
    for p in pending:
        print(f"[{p['at']}] {p['author']}  👍{p['likes']}")
        print(f"  영상: {titles.get(p['vid'], p['vid'])[:60]}")
        print(f"  내용: {p['text'][:240]}")
        print(f"  키   : (\"{p['author']}\", \"{p['vid']}\")")
        print(f"  ID   : {p['cid']}   # 답하지 않을 거면 data/comment_ignore.txt 에 이 ID 추가")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
