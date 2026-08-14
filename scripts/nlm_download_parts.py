#!/usr/bin/env python3
"""범용 NLM 비디오 다운로드 — 인자로 받은 파트 이름들의 노트북에서 비디오 다운로드

사용: python3 download_parts.py "곰브리치_세계사_Part1" "곰브리치_세계사_Part2" ...
(.pipeline_state/{이름}_notebook.json 의 URL 사용, input/{이름}_video_kr.mp4 로 저장)
"""
import asyncio
import json
import sys
from pathlib import Path

PROJECT = Path("/home/jsong/dev/jsong1230-github/booksummary")
sys.path.insert(0, str(PROJECT / "scripts"))
import notebooklm_automator as na  # noqa: E402

PROFILE_DIR = Path.home() / ".notebooklm_chrome_profile"
SESSION_FILE = Path.home() / ".notebooklm_session.json"
STATE_DIR = PROJECT / ".pipeline_state"


def logged_out(url: str) -> bool:
    return "accounts.google.com" in url or "/login" in url


async def main() -> None:
    from playwright.async_api import async_playwright

    names = sys.argv[1:]
    if not names:
        print("사용법: download_parts.py <safe_name>...")
        sys.exit(2)

    results = {}
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            accept_downloads=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-features=BoundSessionCredentials,EnableBoundSessionCredentials,DeviceBoundSessionCredentials",
            ],
        )
        page = await ctx.new_page()

        for safe_name in names:
            print(f"\n===== {safe_name} =====", flush=True)
            out_path = PROJECT / f"input/{safe_name}_video_kr.mp4"
            if out_path.exists():
                print(f"SKIP: 이미 존재 {out_path}", flush=True)
                results[safe_name] = str(out_path)
                continue
            state_file = STATE_DIR / f"{safe_name}_notebook.json"
            if not state_file.exists():
                print(f"FAIL {safe_name}: 노트북 URL 없음", flush=True)
                results[safe_name] = None
                continue
            nb_url = json.loads(state_file.read_text())["url"]
            await page.goto(nb_url, wait_until="load", timeout=60000)
            await page.wait_for_timeout(8000)
            if logged_out(page.url):
                print("LOGIN_NEEDED — 세션 만료", flush=True)
                results[safe_name] = None
                continue
            await na._dismiss_welcome_dialog(page)
            await na._clear_overlays(page)
            video = await na._download_from_menu(page, str(out_path))
            results[safe_name] = video
            print(("OK " if video else "FAIL ") + safe_name, flush=True)

        await ctx.storage_state(path=str(SESSION_FILE))
        await ctx.close()

    print("\nFINAL: " + json.dumps({k: str(v) for k, v in results.items()}, ensure_ascii=False), flush=True)
    if not all(results.values()):
        sys.exit(1)


asyncio.run(main())
