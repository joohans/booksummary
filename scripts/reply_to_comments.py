#!/usr/bin/env python3
"""구독자 댓글에 답글 게시 + 혐오 댓글 숨김 처리.

기본은 --dry-run (미리보기). 실제 게시는 --apply 필요.
답글 문안은 REPLIES 딕셔너리에 (작성자, videoId) 키로 정의한다.
"""
import argparse
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CHANNEL_ID = "UCxOcO_x_yW6sfg_FPUQVqYA"
OWNER = "@BeyondPage_Bi"
CREDS = Path(__file__).resolve().parent.parent / "secrets" / "credentials.json"

# (작성자, videoId) -> 답글 본문
REPLIES = {
    ("@ldrd7", "YIJPtbCwKpA"):
        "맞습니다. 관점을 바꾸라는 조언이 통하지 않는 날이 분명히 있습니다. "
        "괴로운 건 괴로운 채로 두셔도 괜찮습니다. 봐주셔서 감사합니다.",
    ("@지승연-k1o", "JI-IuCEzslY"):
        "완독하고 바로 다시 읽으신다니 반갑습니다. 두 번째로 읽으면 처음엔 지나쳤던 문장들이 "
        "다르게 보이더군요. 감사합니다.",
    ("@choungheeha746", "7E51amuXo68"):
        "읽기 전에 도움이 되셨다면 다행입니다. 감사합니다.",
    ("@여름좋냐", "MEOrrGvwvCY"):
        "1등이시네요. 봐주셔서 감사합니다.",
    ("@이름없어-d1o", "BnovpY5w5ZM"):
        "들어보시고 의견 있으시면 편하게 남겨주세요. 감사합니다.",
    ("@TV-zs3hb", "0HDaR9ZwXMA"):
        "구독과 좋아요까지 남겨주셔서 감사합니다. 큰 힘이 됩니다.",
    ("@Garimtos-g4c", "L8FLJWGj7GE"):
        "봐주셔서 감사합니다. 다음 영상에서도 뵙겠습니다.",
    ("@jungeunhwa7331", "SwtiS91WQCQ"):
        "궁금증이 조금 풀리셨다면 다행입니다. 감사합니다.",
    ("@hzoou", "rvQL6VbtmGo"):
        "우엘백은 요약하기 까다로운 작가인데 도움이 되셨다니 다행입니다. 감사합니다.",
    ("@하이하이-s1o", "8N4yJWdr5NI"):
        "짧은 피드백도 큰 힘이 됩니다. 감사합니다.",
    ("@jjy-xd8df", "1zACX8Hsd6g"):
        "스미스는 분업으로 파이 자체가 커진다고 봤습니다. 다만 커진 파이를 누가 얼마나 갖는지는 "
        "국부론이 답하지 않고 남겨둔 부분이고, 지금까지 논쟁이 이어지는 지점입니다. 의견 감사합니다.",
    ("@주종국-o3u", "1dKsiVS6gP0"):
        "말씀하신 것처럼 요즘은 그런 분위기의 고전 극화를 보기 어렵습니다. "
        "광기와 논리를 함께 쥔 작가라는 표현이 정확하네요. 좋은 회고 감사합니다.",
    ("@마카오-i6h", "1r_oGXMMbKY"):
        "네, 받습니다. 댓글로 남겨주시면 답변드리겠습니다.",
    ("@TheMccormjx", "AlnwaoSecxY"):
        "Thanks for watching. Glad it reached you.",
    ("@chanxpress", "6979rL1-xCM"):
        "Thank you for watching — glad it was useful.",
    ("@gbbchen1070", "hnKNyhKluBg"):
        "Good point. Jin Yong serialized it during the Cultural Revolution, and knowing that "
        "changes how the sect conflicts read. Thanks for adding the context.",
    ("@GloriousViveDigital", "U84k0BSLQ-o"):
        "Thank you. Positioning is something we're working on now — if you have a specific "
        "suggestion, I'd be glad to hear it.",
    ("@anwer6707", "X6dw_z5N2cY"):
        "Sorry, we can't share copies due to copyright. Most libraries carry it, and the links "
        "in the description point to legitimate sellers.",
    # 비판 — 변명 없이 인정
    ("@a4c7v3xzil", "7E51amuXo68"):
        "AI 도구를 쓰는 건 맞습니다. 그렇게 보이셨다면 아직 다듬을 부분이 있다는 뜻으로 "
        "받아들이겠습니다. 지적 감사합니다.",
    ("@dggartist-fz3yb", "FhNzjqLD_Dw"):
        "내용이 늘어졌다는 지적은 받아들입니다. 분량을 채우기보다 핵심을 줄이는 쪽으로 "
        "고쳐가겠습니다. 감사합니다.",
    ("@4davidrosen", "4xKtR72RFoM"):
        "You're right — that was a careless use of the word. Thanks for the correction.",
}

# 숨김(거부) 처리할 댓글: (작성자, videoId) — 혐오 발언
HIDE = {("@KWIATOSTAN-q6v", "7E51amuXo68")}

# 의도적으로 답하지 않음 (순수 악평)
SKIP = {("@rvera3708", "fvgdHbT5vHM")}


def fetch_threads(yt):
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
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제 게시 (기본: 미리보기)")
    args = ap.parse_args()

    yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file(str(CREDS)))
    threads = fetch_threads(yt)

    planned, hide_ids, matched = [], [], set()
    for it in threads:
        top = it["snippet"]["topLevelComment"]
        sn = top["snippet"]
        author, vid = sn["authorDisplayName"], sn["videoId"]
        if author == OWNER:
            continue
        key = (author, vid)
        already = any(
            r["snippet"]["authorDisplayName"] == OWNER
            for r in it.get("replies", {}).get("comments", [])
        )
        if key in HIDE:
            hide_ids.append((top["id"], author))
            matched.add(key)
        elif key in REPLIES and not already:
            planned.append((top["id"], author, vid, REPLIES[key]))
            matched.add(key)
        elif key in REPLIES and already:
            matched.add(key)

    missing = set(REPLIES) - matched
    print(f"답글 예정 {len(planned)}건 / 숨김 예정 {len(hide_ids)}건")
    if missing:
        print(f"⚠️ 매칭 실패 {len(missing)}건: {sorted(missing)}")

    for cid, author, vid, body in planned:
        print(f"\n  → {author} ({vid})\n    {body[:100]}")
    for cid, author in hide_ids:
        print(f"\n  ✂ 숨김: {author} ({cid})")

    if not args.apply:
        print("\n[미리보기] 실제 게시는 --apply")
        return 0

    ok = err = 0
    for cid, author, vid, body in planned:
        try:
            yt.comments().insert(
                part="snippet",
                body={"snippet": {"parentId": cid, "textOriginal": body}},
            ).execute()
            print(f"✅ {author}")
            ok += 1
        except Exception as e:
            print(f"❌ {author}: {str(e)[:140]}")
            err += 1

    for cid, author in hide_ids:
        try:
            yt.comments().setModerationStatus(id=cid, moderationStatus="rejected").execute()
            print(f"✂ 숨김 완료: {author}")
        except Exception as e:
            print(f"❌ 숨김 실패 {author}: {str(e)[:140]}")
            err += 1

    print(f"\n답글 {ok}건 성공 / 실패 {err}건")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
