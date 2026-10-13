#!/usr/bin/env python3
"""「숙향전」 예약 업로드 1회성 작업 (2026-10-13 16:05 KST 실행, 할당량 리셋 후)

사용자 결정(B안): 고전소설 시리즈 2 가 끊기지 않게 배비장전(11/12) 다음 날 11/13 에 넣고,
11/13 이후 예약 13편을 하루씩 민다.

순서: 하루 밀기 → 11/13 비었는지 확인 → 업로드 → 90초 뒤 태그·예약 재확인(부족하면 재전송)
     → 재생목록 2곳 → 배비장전 설명란 「▶ 다음: 준비 중」→「▶ 다음: 숙향전 (11/13)」 → series_gojeon.json

    setsid nohup bash -c 'sleep N; .venv/bin/python scripts/publish_sukhyang_job.py' > /tmp/sukhyang_job.log 2>&1 &
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from google.oauth2.credentials import Credentials  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402

from shift_schedule import scheduled_videos  # noqa: E402

META = ROOT / "output/The_Tale_of_Suk_Hyang_kr.metadata.json"
PUBLISH = "2026-11-13T09:00:00Z"
PL_SERIES = "PLDQMbH9G5tlg"
PL_ALL = "PLrZ4eky3zPhJkKccHEIMN2bQPNPzFPzxT"
BAEBIJANG = "-XUjmj7O_TU"
SNIPPET_KEYS = ("title", "description", "tags", "categoryId", "defaultLanguage", "defaultAudioLanguage")


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def yt():
    return build("youtube", "v3", credentials=Credentials.from_authorized_user_file(str(ROOT / "secrets/credentials.json")))


def main() -> int:
    py = str(ROOT / ".venv/bin/python")
    y = yt()

    # 1) 이미 올라갔는지(재실행 방지)
    if any("숙향전" in t for _, t, _, _ in scheduled_videos(y)):
        log("⛔ 숙향전이 이미 예약돼 있다 — 중단")
        return 1

    # 2) 11/13 이후 하루 밀기
    r = subprocess.run([py, "scripts/shift_schedule.py", "--from", "2026-11-13", "--days", "1", "--apply"],
                       cwd=ROOT, capture_output=True, text=True)
    log("shift rc", r.returncode, r.stdout[-600:], r.stderr[-600:])
    if r.returncode != 0:
        return 1
    time.sleep(30)
    days = [pa[:10] for pa, *_ in scheduled_videos(y)]
    if "2026-11-13" in days:
        log("⛔ 밀기 후에도 11/13 이 차 있다 — 업로드 중단", days)
        return 1
    log("11/13 비었음, 예약", len(days), "편, 끝", days[-1])

    # 3) 업로드
    m = json.loads(META.read_text())
    m["publish_at"] = PUBLISH
    META.write_text(json.dumps(m, ensure_ascii=False, indent=2))
    r = subprocess.run([py, "src/09_upload_from_metadata.py", "--privacy", "private", "--auto",
                        "--metadata-files", str(META.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True)
    out = r.stdout + r.stderr
    log("upload rc", r.returncode, out[-1500:])
    ids = re.findall(r"업로드 완료: https://www.youtube.com/watch\?v=([A-Za-z0-9_-]{11})", out)
    if not ids:
        log("⛔ 영상 ID 를 찾지 못했다 — 이후 단계 중단")
        return 1
    vid = ids[-1]
    log("영상", vid)

    # 4) 90초 뒤 재확인
    time.sleep(90)
    v = y.videos().list(part="snippet,status", id=vid).execute()["items"][0]
    tags = v["snippet"].get("tags", [])
    log("tags", len(tags), "status", v["status"].get("privacyStatus"), v["status"].get("publishAt"))
    if len(tags) < len(m["tags"]):
        sn = {k: v["snippet"][k] for k in SNIPPET_KEYS if k in v["snippet"]}
        sn["tags"] = m["tags"]
        y.videos().update(part="snippet", body={"id": vid, "snippet": sn}).execute()
        time.sleep(60)
        log("tags 재전송 후", len(y.videos().list(part="snippet", id=vid).execute()["items"][0]["snippet"].get("tags", [])))

    # 5) 재생목록
    for pl in (PL_SERIES, PL_ALL):
        y.playlistItems().insert(part="snippet", body={"snippet": {
            "playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
        log("playlist 추가", pl)

    # 6) 배비장전 설명란
    b = y.videos().list(part="snippet", id=BAEBIJANG).execute()["items"][0]["snippet"]
    old = "▶ 다음: 준비 중"
    if old in b["description"]:
        sn = {k: b[k] for k in SNIPPET_KEYS if k in b}
        sn["description"] = b["description"].replace(old, "▶ 다음: 숙향전 (11/13)", 1)
        y.videos().update(part="snippet", body={"id": BAEBIJANG, "snippet": sn}).execute()
        log("배비장전 설명란 갱신")
    else:
        log("⚠️ 배비장전 설명란에 「다음: 준비 중」이 없다 — 손대지 않음")

    # 7) series_gojeon.json
    p = ROOT / "data/series_gojeon.json"
    s = json.loads(p.read_text())
    if not any(e.get("video_id") == vid for e in s.get("series2", [])):
        s["series2"].append({"title": "숙향전", "video_id": vid, "date": "11/13"})
        p.write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n")
        log("series_gojeon.json 갱신")

    # 8) 최종 확인
    time.sleep(30)
    v = y.videos().list(part="snippet,status", id=vid).execute()["items"][0]
    b = y.videos().list(part="snippet", id=BAEBIJANG).execute()["items"][0]["snippet"]["description"]
    log("최종", vid, len(v["snippet"].get("tags", [])), v["status"].get("publishAt"),
        "썸네일", list(v["snippet"]["thumbnails"].keys()), "배비장전 다음:", "숙향전 (11/13)" in b)
    log("✅ 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
