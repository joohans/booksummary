#!/usr/bin/env python3
"""일당백 에피소드 NLM 원샷 파이프라인 — 로그인 유지 상태에서 N개 파트 생성+다운로드 일괄 처리

세션 쿠키가 브라우저 재시작마다 무효화(DBSC 로테이션)되므로,
브라우저 한 번 실행으로 로그인부터 모든 파트 비디오 생성·다운로드까지 처리한다.

사용:
    DISPLAY=:99 python3 scripts/nlm_episode_oneshot.py --title "사랑의 학교" --parts 2
    # 특정 파트만: --only 3

사전 조건:
    - data/notebooklm_urls/{제목_언더스코어}_part{N}_ko.md 소스 파일 존재
    - ~/.notebooklm_chrome_profile 에 Google 로그인 세션 (만료 시 VNC 로그인 안내 출력)

출력: input/{제목_언더스코어}_Part{N}_video_kr.mp4

멈춘 생성(스피너 지속) 대응: 해당 파트만 --only 로 재실행하면 새 노트북으로 재생성된다.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "scripts"))
import notebooklm_automator as na  # noqa: E402

PROFILE_DIR = Path.home() / ".notebooklm_chrome_profile"
SESSION_FILE = Path.home() / ".notebooklm_session.json"


def logged_out(url: str) -> bool:
    return "accounts.google.com" in url or "/login" in url


async def run(title: str, part_nums: list[int]) -> None:
    from playwright.async_api import async_playwright

    safe = title.replace(" ", "_")
    parts = [
        (f"{title} Part{i}",
         PROJECT / f"data/notebooklm_urls/{safe}_part{i}_ko.md",
         PROJECT / f"input/{safe}_Part{i}_video_kr.mp4")
        for i in part_nums
    ]
    for _, urls_file, _ in parts:
        if not urls_file.exists():
            print(f"❌ 소스 파일 없음: {urls_file}")
            sys.exit(2)

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
        await page.goto(na.NOTEBOOKLM_URL, wait_until="load", timeout=60000)
        await page.wait_for_timeout(5000)

        if logged_out(page.url):
            print("LOGIN_NEEDED — Xvfb+x11vnc 띄우고 VNC로 로그인하세요 (최대 20분 대기)", flush=True)
            for _ in range(400):
                if not logged_out(page.url) and "notebook.google.com" in page.url:
                    break
                await page.wait_for_timeout(3000)
        if logged_out(page.url):
            print("RESULT: LOGIN_TIMEOUT", flush=True)
            await ctx.close()
            sys.exit(2)

        print("LOGIN_OK", flush=True)
        await ctx.storage_state(path=str(SESSION_FILE))
        (PROFILE_DIR / ".seeded").touch()

        results = {}
        for part_title, urls_file, out_path in parts:
            print(f"\n===== {part_title} =====", flush=True)
            if out_path.exists():
                print(f"SKIP: 이미 존재 {out_path}", flush=True)
                results[part_title] = str(out_path)
                continue
            urls = na.extract_urls_from_md(str(urls_file))
            print(f"소스 URL {len(urls)}개", flush=True)

            await page.goto(na.NOTEBOOKLM_URL, wait_until="load", timeout=60000)
            await page.wait_for_timeout(3000)
            await na._wait_for_page_ready(page, timeout_ms=60000)

            if not await na._click_new_notebook(page):
                print(f"FAIL {part_title}: 새 노트북 생성 실패", flush=True)
                results[part_title] = None
                continue
            await page.wait_for_timeout(5000)
            na._save_notebook_url(part_title, page.url)
            print(f"노트북 URL: {page.url[:70]}", flush=True)

            added = await na._add_sources(page, urls)
            print(f"추가된 소스: {added}", flush=True)
            if added == 0:
                print(f"FAIL {part_title}: 소스 추가 실패", flush=True)
                results[part_title] = None
                continue

            video = await na._generate_and_download_video(page, str(out_path))
            results[part_title] = video
            print(("OK " if video else "FAIL ") + part_title + f": {video}", flush=True)
            await ctx.storage_state(path=str(SESSION_FILE))

        await ctx.storage_state(path=str(SESSION_FILE))
        await ctx.close()
        print("\nFINAL: " + json.dumps({k: str(v) for k, v in results.items()}, ensure_ascii=False), flush=True)
        if not all(results.values()):
            sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description="일당백 NLM 파트 비디오 원샷 생성")
    ap.add_argument("--title", required=True, help="책 제목 (예: 사랑의 학교)")
    ap.add_argument("--parts", type=int, default=2, help="파트 수 (기본 2)")
    ap.add_argument("--only", type=int, help="특정 파트만 재실행 (새 노트북 재생성)")
    args = ap.parse_args()
    nums = [args.only] if args.only else list(range(1, args.parts + 1))
    asyncio.run(run(args.title, nums))


if __name__ == "__main__":
    main()
