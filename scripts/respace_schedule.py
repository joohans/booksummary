#!/usr/bin/env python3
"""예약 공개 간격 재배치 — 순서는 유지하고 날짜만 N일 간격으로 다시 깐다.

--start 이후(KST, 경계 포함)의 예약 편을 현재 순서대로 --start 부터 --every 일 간격,
--time 시각에 다시 배정한다. 고전소설 시리즈 설명란의 「◀ 이전: 책 (M/D)」「▶ 다음: 책 (M/D)」
날짜도 새 일정에 맞춰 고친다.

status 는 기존 값을 전부 보존해서 보낸다. videos.update 는 빠진 필드를 기본값으로
덮어쓰므로 embeddable·publicStatsViewable·license 를 빠뜨리면 False 로 바뀐다.

    # 미리보기 (기본)
    .venv/bin/python scripts/respace_schedule.py --start 2026-10-13 --every 1
    # 실제 적용
    .venv/bin/python scripts/respace_schedule.py --start 2026-10-13 --every 1 --apply
"""
import argparse
import re
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from shift_schedule import KST, STATUS_KEYS, scheduled_videos

SNIPPET_KEYS = ("title", "description", "tags", "categoryId", "defaultLanguage", "defaultAudioLanguage")


def book_name(title: str) -> str:
    """'[핵심 요약] 박씨전: 작자 미상 (...)' → '박씨전'"""
    t = re.sub(r"^\[[^\]]*\]\s*", "", title)
    return re.split(r"[:(]", t, maxsplit=1)[0].strip()


def fix_description(desc: str, new_dates: dict) -> str:
    """시리즈 이동 줄의 「책 (M/D」 날짜를 새 일정으로 바꾼다."""
    def repl(m):
        name = m.group(2).strip()
        if name not in new_dates:
            return m.group(0)
        return f"{m.group(1)}{m.group(2)}({new_dates[name]:%-m/%d}"

    out = []
    for line in desc.splitlines():
        if "◀" in line or "▶" in line:
            line = re.sub(r"((?:◀ 이전|▶ 다음):\s*)([^(|]+?\s)\(\d{1,2}/\d{1,2}", repl, line)
        out.append(line)
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="첫 배정일(KST, YYYY-MM-DD). 이 날짜 이후 예약 편이 대상")
    ap.add_argument("--every", type=int, default=1, help="간격(일)")
    ap.add_argument("--time", default="18:00", help="공개 시각(KST, HH:MM)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    hh, mm = map(int, args.time.split(":"))
    start = datetime.strptime(args.start, "%Y-%m-%d").replace(hour=hh, minute=mm, tzinfo=KST)
    creds = Credentials.from_authorized_user_file("secrets/credentials.json")
    yt = build("youtube", "v3", credentials=creds)

    sched = scheduled_videos(yt)
    targets = []
    for pa, title, vid, v in sched:
        cur = datetime.fromisoformat(pa.replace("Z", "+00:00")).astimezone(KST)
        if cur >= start.replace(hour=0, minute=0):
            new = start + timedelta(days=args.every * len(targets))
            targets.append((cur, new, title, vid, v))

    new_dates = {book_name(t[2]): t[1] for t in targets}
    print(f"대상 {len(targets)}편 → {args.every}일 간격 {args.time} KST\n")
    plan = []
    for cur, new, title, vid, v in targets:
        desc = v["snippet"].get("description", "")
        fixed = fix_description(desc, new_dates)
        plan.append((new, title, vid, v, fixed if fixed != desc else None))
        mark = "  [설명란 날짜 수정]" if fixed != desc else ""
        print(f"  {cur:%m/%d %a} → {new:%m/%d %a}  {title[:44]}{mark}")
        if fixed != desc:
            for a, b in zip(desc.splitlines(), fixed.splitlines()):
                if a != b:
                    print(f"      - {a.strip()}\n      + {b.strip()}")

    if not args.apply:
        print("\n미리보기입니다. 실제 적용하려면 --apply 를 붙이세요.")
        return

    print()
    for new, title, vid, v, fixed in plan:
        status = {k: v["status"][k] for k in STATUS_KEYS if k in v["status"]}
        status["publishAt"] = new.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        body = {"id": vid, "status": status}
        part = "status"
        if fixed is not None:
            # snippet 도 빠진 필드가 지워지므로 기존 값을 전부 실어 보낸다
            snippet = {k: v["snippet"][k] for k in SNIPPET_KEYS if k in v["snippet"]}
            snippet["description"] = fixed
            body["snippet"] = snippet
            part = "snippet,status"
        yt.videos().update(part=part, body=body).execute()
        print(f"  ✅ {new:%m/%d %a} {title[:42]}")
    print(f"\n{len(plan)}편 재배치 완료")


if __name__ == "__main__":
    main()
