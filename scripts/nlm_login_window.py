#!/usr/bin/env python3
"""NLM(Gemini Notebook) 재로그인 창 — VNC 로 사람이 로그인하도록 브라우저를 띄워 두고 기다린다.

oneshot 과 같은 Playwright 설정·프로필(~/.notebooklm_chrome_profile)로 띄운다.
(2026-10-04 실측: chrome 바이너리를 직접 띄우면 페이지가 그려지지 않고 로딩에서 멈췄다.
 같은 머신에서 Playwright 로 띄운 창은 정상.)

로그인이 끝나 notebook.google.com 의 노트북 목록이 보이면 스스로 닫는다(최대 30분).
닫힌 뒤 nlm_episode_oneshot.py 를 다시 실행하면 쿠키가 남아 바로 LOGIN_OK 로 통과한다.

사용법: DISPLAY=:99 python3 -u scripts/nlm_login_window.py
"""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".notebooklm_chrome_profile"
LOGIN_URL = "https://accounts.google.com/ServiceLogin?continue=https%3A%2F%2Fnotebook.google.com%2F"


async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-dev-shm-usage", "--no-sandbox",
                  "--disable-features=BoundSessionCredentials,EnableBoundSessionCredentials,DeviceBoundSessionCredentials"])
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto(LOGIN_URL, wait_until="load", timeout=60000)
        print("LOGIN_WINDOW_OPEN", flush=True)
        for i in range(360):  # 5초 × 360 = 30분
            await asyncio.sleep(5)
            for pg in ctx.pages:
                url = pg.url
                if url.startswith("https://notebook.google.com") and "/trynow" not in url and "accounts." not in url:
                    has_new = await pg.evaluate(
                        "() => Array.from(document.querySelectorAll('button')).some(b => /새 노트북|노트북 만들기|Create new|New notebook/.test(b.innerText||''))")
                    if has_new:
                        print(f"LOGIN_DONE {url}", flush=True)
                        await asyncio.sleep(3)
                        await ctx.close()
                        return
            if i % 12 == 0:
                print(f"waiting… {[pg.url[:60] for pg in ctx.pages]}", flush=True)
        print("LOGIN_TIMEOUT", flush=True)
        await ctx.close()


if __name__ == "__main__":
    asyncio.run(main())
