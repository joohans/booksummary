"""
NotebookLM Video Overview 자동화 스크립트
Playwright를 사용하여 NotebookLM에서 비디오를 자동으로 생성하고 다운로드합니다.

핵심 전략:
  - page.evaluate() (JavaScript) 기반 요소 탐색/클릭 → 오버레이 우회
  - 매 단계 전 오버레이 강제 정리
  - 재시도 로직 + 노트북 URL 저장으로 복구 지원

사용법:
  python scripts/notebooklm_automator.py --login
  python scripts/notebooklm_automator.py --book-title "책 제목" --language ko --urls-file "path.md"
  python scripts/notebooklm_automator.py --book-title "책 제목" --notebook-url "https://..."  # 기존 노트북 재사용
"""

import os
import sys
import time
import asyncio
import argparse
import json as json_module
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

_session_env = os.environ.get("NOTEBOOKLM_SESSION_FILE")
SESSION_FILE = Path(_session_env) if _session_env else Path.home() / ".notebooklm_session.json"
_profile_env = os.environ.get("NOTEBOOKLM_PROFILE_DIR")
DEFAULT_PROFILE_DIR = Path(_profile_env) if _profile_env else Path.home() / ".notebooklm_chrome_profile"
# 2026-08: NotebookLM → Gemini Notebook 리브랜딩, notebook.google.com으로 도메인 변경
# 구 도메인 경유 시 로그인 재확인 플로우(accountchooser)로 빠지므로 신 도메인 직행 필수
NOTEBOOKLM_URL = "https://notebook.google.com"
MAX_WAIT_MINUTES = 60
STATE_DIR = Path(__file__).parent.parent / ".pipeline_state"


# ─────────────────────────────────────────────────────────────
# 유틸리티
# ─────────────────────────────────────────────────────────────

def _notify(msg: str, title: str = "NotebookLM 자동화", success: bool = True):
    """알림 (macOS: osascript, Linux: print)"""
    import platform
    status = "✅" if success else "❌"
    print(f"{status} [{title}] {msg}")
    if platform.system() != "Darwin":
        return
    import subprocess
    sound = "Glass" if success else "Basso"
    script = f'display notification "{msg}" with title "{title}" sound name "{sound}"'
    subprocess.run(["osascript", "-e", script], check=False)
    subprocess.run(["afplay", f"/System/Library/Sounds/{sound}.aiff"], check=False)


def extract_urls_from_md(md_path: str) -> list[str]:
    """MD 파일에서 URL 목록 추출"""
    import re
    urls = []
    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                urls.append(line)
            elif "](http" in line:
                matches = re.findall(r'\((https?://[^\)]+)\)', line)
                urls.extend(matches)
    return urls[:20]


async def _screenshot(page, name: str) -> str:
    """디버그 스크린샷 저장"""
    path = Path("output/debug") / f"{name}_{int(time.time())}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        await page.screenshot(path=str(path))
        print(f"   📸 {path}")
    except Exception:
        print(f"   📸 스크린샷 실패: {path}")
    return str(path)


def _save_notebook_url(book_title: str, url: str):
    """노트북 URL을 state에 저장 (resume 지원)"""
    STATE_DIR.mkdir(exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in book_title)
    state_file = STATE_DIR / f"{safe}_notebook.json"
    state_file.write_text(json_module.dumps({"url": url, "ts": time.time()}))


def _load_notebook_url(book_title: str) -> Optional[str]:
    """저장된 노트북 URL 로드"""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in book_title)
    state_file = STATE_DIR / f"{safe}_notebook.json"
    if state_file.exists():
        data = json_module.loads(state_file.read_text())
        # 24시간 이내만 유효
        if time.time() - data.get("ts", 0) < 86400:
            return data.get("url")
    return None


# ─────────────────────────────────────────────────────────────
# 핵심: JavaScript 기반 DOM 조작 (오버레이 우회)
# ─────────────────────────────────────────────────────────────

async def _clear_overlays(page):
    """모든 오버레이/모달/컨텍스트 메뉴 강제 제거"""
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        # Angular CDK 오버레이 backdrop 강제 제거
        await page.evaluate("""
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-pane:empty').forEach(el => el.remove());
            document.querySelectorAll('[class*="context-menu"]').forEach(el => el.remove());
        """)
        await page.wait_for_timeout(200)
    except Exception:
        pass


async def _js_find_and_click(page, text: str, tag: str = "*") -> bool:
    """JavaScript로 텍스트를 포함한 요소를 찾아 클릭 (오버레이 우회)

    Playwright CSS 셀렉터 대신 JS로 직접 DOM 탐색.
    element.click() 대신 dispatchEvent로 클릭하므로 backdrop 무시.
    """
    result = await page.evaluate(f"""
        (() => {{
            const text = {json_module.dumps(text)};
            const tag = {json_module.dumps(tag)};
            const all = document.querySelectorAll(tag);
            for (const el of all) {{
                // 요소의 직접 텍스트만 비교 (자식 제외하면 너무 strict하므로 innerText 사용)
                if (el.innerText && el.innerText.trim().includes(text) && el.offsetParent !== null) {{
                    el.dispatchEvent(new MouseEvent('click', {{bubbles: true, cancelable: true}}));
                    return el.tagName + ': ' + el.innerText.trim().substring(0, 50);
                }}
            }}
            return null;
        }})()
    """)
    if result:
        print(f"   JS click: {result[:60]}")
        return True
    return False


async def _js_find_and_click_specific(page, text: str) -> bool:
    """JS 클릭 - 텍스트를 포함하는 카드/버튼 요소를 네이티브 click()으로 클릭

    전략: 텍스트를 포함하는 가장 작은 SPAN/라벨을 찾은 후,
    그 부모 중 클릭 가능한 카드/버튼 요소를 찾아 .click() 호출.
    (dispatchEvent 대신 .click() 사용 → Angular 이벤트 핸들러 트리거)
    """
    result = await page.evaluate(f"""
        (() => {{
            const text = {json_module.dumps(text)};

            // 1. 텍스트를 직접 포함하는 가장 작은 요소 찾기
            let bestLabel = null;
            let bestSize = Infinity;
            const all = document.querySelectorAll('span, div, p, h1, h2, h3, button, a');
            for (const el of all) {{
                // 직접 텍스트 노드만 확인 (자식 요소의 텍스트 제외)
                const directText = Array.from(el.childNodes)
                    .filter(n => n.nodeType === 3)
                    .map(n => n.textContent.trim())
                    .join(' ');
                const fullText = (el.innerText || '').trim();

                if (!fullText.includes(text)) continue;
                if (el.offsetParent === null) continue;

                const rect = el.getBoundingClientRect();
                const size = rect.width * rect.height;
                if (size < 10 || size > 200000) continue;

                // 직접 텍스트가 있는 요소 우선
                const priority = directText.includes(text) ? 0 : size;
                const score = directText.includes(text) ? size : size + 1000000;

                if (score < bestSize) {{
                    bestLabel = el;
                    bestSize = score;
                }}
            }}

            if (!bestLabel) return null;

            // 2. 부모 체인에서 클릭 가능한 카드/버튼 컨테이너 찾기
            let clickTarget = bestLabel;
            let parent = bestLabel.parentElement;
            for (let i = 0; i < 5 && parent; i++) {{
                const tag = parent.tagName.toLowerCase();
                const role = parent.getAttribute('role') || '';
                const cls = parent.className || '';

                // mat-card, button, [role=button], 클릭 가능한 컨테이너
                if (tag === 'button' || tag === 'a' ||
                    tag.includes('mat-card') || tag.includes('mat-button') ||
                    role === 'button' || role === 'listitem' ||
                    cls.includes('card') || cls.includes('chip') ||
                    cls.includes('output-type') || cls.includes('studio')) {{
                    clickTarget = parent;
                    break;
                }}
                parent = parent.parentElement;
            }}

            // 3. 네이티브 .click() 호출 (dispatchEvent 대신)
            clickTarget.click();

            const labelInfo = bestLabel.tagName + '(' + Math.round(bestLabel.getBoundingClientRect().width * bestLabel.getBoundingClientRect().height) + 'px)';
            const targetInfo = clickTarget.tagName + '.' + (clickTarget.className || '').substring(0, 30);
            return 'label=' + labelInfo + ' → target=' + targetInfo + ': ' + bestLabel.innerText.trim().substring(0, 30);
        }})()
    """)
    if result:
        print(f"   JS click: {result[:80]}")
        return True
    return False


async def _find_button(page, selectors: list[str], timeout: int = 2000):
    """여러 CSS 셀렉터를 순서대로 시도해 요소 반환"""
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=timeout):
                return btn
        except Exception:
            continue
    return None


# ─────────────────────────────────────────────────────────────
# 로그인
# ─────────────────────────────────────────────────────────────

def login(headless: bool = False):
    """최초 1회 Google 로그인 → Chrome 프로필 + session 파일 저장"""
    from playwright.sync_api import sync_playwright

    print("🔐 Google 로그인 세션 생성 중...")
    print("   브라우저에서 Google 계정으로 로그인하세요.")
    print("   NotebookLM 메인 페이지가 열리면 자동으로 세션이 저장됩니다. (최대 3분)")

    PROFILE_DIR = DEFAULT_PROFILE_DIR
    PROFILE_DIR.mkdir(exist_ok=True)
    # 이전 seed 마커 제거해서 다음 실행 시 재seed 방지
    seeded = PROFILE_DIR / ".seeded"
    if seeded.exists():
        seeded.unlink()

    with sync_playwright() as p:
        # Chrome 프로필을 사용해서 로그인 — 이후 자동화와 동일한 프로필 사용
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        page = context.new_page()
        page.goto(NOTEBOOKLM_URL)

        try:
            page.wait_for_url(
                lambda url: "notebooklm.google.com" in url and "accounts.google.com" not in url,
                timeout=180000,
            )
            print("✅ 로그인 감지! 세션 저장 중...")
            page.wait_for_timeout(2000)
        except Exception:
            print("⚠️  3분 내 로그인 미감지. 현재 상태로 세션 저장.")

        # Chrome 프로필에 이미 세션이 저장됨. 쿠키도 파일로 백업
        context.storage_state(path=str(SESSION_FILE))
        # seed 완료 마커
        (PROFILE_DIR / ".seeded").touch()
        context.close()

    print(f"✅ 세션 저장 완료: {SESSION_FILE}")
    print(f"✅ Chrome 프로필 저장 완료: {PROFILE_DIR}")


# ─────────────────────────────────────────────────────────────
# Step 1: 페이지 접속 + 로드 대기
# ─────────────────────────────────────────────────────────────

async def _dismiss_welcome_dialog(page) -> None:
    """환영 다이얼로그 닫기 (있을 경우)"""
    try:
        clicked = await _js_find_and_click(page, "확인", "button")
        if not clicked:
            clicked = await _js_find_and_click(page, "Got it", "button")
        if not clicked:
            # Gemini Notebook 리브랜딩 안내 다이얼로그 (2026-08 확인)
            clicked = await _js_find_and_click(page, "시작하기", "button")
        if clicked:
            print("   ✅ 환영 다이얼로그 닫음")
            await page.wait_for_timeout(1500)
    except Exception:
        pass


async def _wait_for_page_ready(page, timeout_ms: int = 60000) -> bool:
    """메인 페이지 로드 완료 대기"""
    print("   ⏳ 페이지 로드 대기 중...")
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        ready = await page.evaluate("""
            (() => {
                // 노트북 생성 버튼 또는 소스 추가 버튼이 있으면 준비됨
                const keywords = [
                    '새로 만들기', 'Create new',
                    '노트북 만들기', 'New notebook',
                    '소스 추가', 'Add source'
                ];
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    if (b.innerText) {
                        for (const kw of keywords) {
                            if (b.innerText.includes(kw)) return true;
                        }
                    }
                }
                return false;
            })()
        """)
        if ready:
            print("   ✅ 페이지 준비됨")
            await _dismiss_welcome_dialog(page)
            await page.wait_for_timeout(1000)
            return True
        await page.wait_for_timeout(2000)

    print("   ⚠️ 페이지 로드 타임아웃")
    return False


# ─────────────────────────────────────────────────────────────
# Step 2: 새 노트북 생성
# ─────────────────────────────────────────────────────────────

async def _click_new_notebook(page) -> bool:
    """새 노트북 생성 → JS 클릭. 이미 빈 노트북 페이지라면 그냥 사용."""
    await _clear_overlays(page)

    # 이미 노트북 내부에 있고 소스가 0개면 그대로 사용
    already_in_notebook = await page.evaluate("""
        (() => {
            const addSource = document.querySelector('button');
            if (!addSource) return false;
            const btns = Array.from(document.querySelectorAll('button'));
            return btns.some(b => b.innerText && (b.innerText.includes('소스 추가') || b.innerText.includes('Add source')));
        })()
    """)
    if already_in_notebook:
        print("   ✅ 이미 노트북 페이지에 있음 (새 노트북 생성 생략)")
        return True

    clicked = await _js_find_and_click(page, "새로 만들기", "button")
    if not clicked:
        clicked = await _js_find_and_click(page, "Create new", "button")
    if not clicked:
        clicked = await _js_find_and_click(page, "노트북 만들기", "button")
    if not clicked:
        clicked = await _js_find_and_click(page, "New notebook", "button")
    if not clicked:
        # CSS 셀렉터 폴백
        btn = await _find_button(page, [
            "button:has-text('새로 만들기')",
            "button:has-text('Create new')",
            "button:has-text('노트북 만들기')",
            "button.create-new-button",
        ], timeout=5000)
        if btn:
            await btn.click(force=True)
            clicked = True

    if clicked:
        print("   ✅ 새 노트북 버튼 클릭")
    else:
        await _screenshot(page, "err_new_notebook")
        print("   ❌ 새 노트북 버튼 없음")
    return clicked


# ─────────────────────────────────────────────────────────────
# Step 3: 소스 URL 추가 (모든 URL 한번에)
# ─────────────────────────────────────────────────────────────

async def _open_url_modal(page) -> bool:
    """'웹사이트 및 YouTube URL' 모달 열기"""
    await _clear_overlays(page)

    # 경로 A: "+ 소스 추가" 버튼 클릭 → "웹사이트" 선택
    clicked = await _js_find_and_click(page, "소스 추가", "button")
    if clicked:
        await page.wait_for_timeout(2000)
        # "웹사이트" 버튼 클릭
        ws_clicked = await _js_find_and_click(page, "웹사이트", "button")
        if ws_clicked:
            await page.wait_for_timeout(1500)
            return True

    # 경로 B: globe 버튼 (aria-label="출처 추가") → force click
    globe_btn = await _find_button(page, [
        "button[aria-label='출처 추가']",
        "button.add-source-button",
    ], timeout=5000)
    if globe_btn:
        await globe_btn.click(force=True)
        await page.wait_for_timeout(2000)

        # textarea가 바로 나타났는지 확인
        try:
            textarea = page.locator("textarea").first
            if await textarea.is_visible(timeout=3000):
                return True
        except Exception:
            pass

        # "웹사이트" 버튼 클릭
        ws_clicked = await _js_find_and_click(page, "웹사이트", "button")
        if ws_clicked:
            await page.wait_for_timeout(1500)
            return True

    return False


async def _add_single_url(page, url: str) -> bool:
    """단일 URL 추가: 모달 열기 → URL 입력 → 삽입 → 닫기

    주의: CDK 오버레이 모달 내부의 textarea를 정확히 타겟팅해야 함.
    좌측 패널의 검색 textarea (placeholder="웹에서 새 소스를 검색하세요")와 혼동 금지.
    """

    # 1. 모달 열기
    opened = await _open_url_modal(page)
    if not opened:
        return False

    # 2. 모달 내부의 textarea/input에 URL 입력 (JS로 직접 조작 - 오버레이 우회)
    input_result = await page.evaluate(f"""
        (() => {{
            const url = {json_module.dumps(url)};

            // CDK 오버레이 모달 내부의 textarea/input 찾기
            const overlay = document.querySelector('.cdk-overlay-pane');
            if (!overlay) return 'no_overlay';

            // 모달 내 textarea 또는 input[type=url/text] 찾기
            const fields = overlay.querySelectorAll('textarea, input[type="text"], input[type="url"], input:not([type])');
            for (const field of fields) {{
                // 검색 필드 제외 (discoverSourcesQuery)
                if (field.getAttribute('formcontrolname') === 'discoverSourcesQuery') continue;
                if ((field.placeholder || '').includes('검색')) continue;

                // URL 입력 필드 발견
                field.focus();
                field.value = url;
                field.dispatchEvent(new Event('input', {{bubbles: true}}));
                field.dispatchEvent(new Event('change', {{bubbles: true}}));
                field.dispatchEvent(new KeyboardEvent('keyup', {{bubbles: true}}));
                return 'filled: ' + field.tagName + '[' + (field.placeholder || field.name || '').substring(0, 30) + ']';
            }}

            // 모달 내 모든 필드 목록 (디버그용)
            const allFields = overlay.querySelectorAll('textarea, input');
            const info = Array.from(allFields).map(f =>
                f.tagName + '[' + (f.placeholder || f.name || 'no-name').substring(0, 25) + ']'
            ).join(', ');
            return 'no_url_field|fields:' + info;
        }})()
    """)
    print(f"      입력: {input_result[:60]}")

    if not input_result or input_result.startswith('no_'):
        await _screenshot(page, "err_url_input")
        return False

    await page.wait_for_timeout(2000)

    # 3. "삽입" 버튼 활성화 대기 + 클릭 (CDK 오버레이 내)
    insert_clicked = await page.evaluate("""
        (() => {
            const overlay = document.querySelector('.cdk-overlay-pane');
            if (!overlay) return null;

            const btns = overlay.querySelectorAll('button');
            for (const btn of btns) {
                const txt = (btn.innerText || '').trim();
                if (txt === '삽입' || txt === 'Insert' || txt === '추가' || txt === 'Add') {
                    if (!btn.disabled) {
                        btn.click();
                        return 'clicked: ' + txt;
                    }
                    return 'disabled: ' + txt;
                }
            }
            return 'no_insert_btn';
        })()
    """)
    print(f"      삽입: {insert_clicked}")

    if insert_clicked and insert_clicked.startswith('clicked'):
        await page.wait_for_timeout(5000)
        return True

    # 비활성화 상태면 대기 후 재시도
    if insert_clicked and 'disabled' in insert_clicked:
        for _ in range(10):
            await page.wait_for_timeout(2000)
            result = await page.evaluate("""
                (() => {
                    const overlay = document.querySelector('.cdk-overlay-pane');
                    if (!overlay) return 'no_overlay';
                    const btns = overlay.querySelectorAll('button');
                    for (const btn of btns) {
                        const txt = (btn.innerText || '').trim();
                        if (txt === '삽입' || txt === 'Insert' || txt === '추가' || txt === 'Add') {
                            if (!btn.disabled) {
                                btn.click();
                                return 'clicked: ' + txt;
                            }
                            return 'still_disabled';
                        }
                    }
                    return 'no_btn';
                })()
            """)
            if result and result.startswith('clicked'):
                await page.wait_for_timeout(5000)
                return True
            if result == 'no_overlay' or result == 'no_btn':
                break

    # 최후 수단: Enter
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(5000)
    return True


async def _add_sources(page, urls: list[str]) -> int:
    """소스 URL 추가 - URL을 하나씩 추가"""
    print("   소스 추가 중...")
    max_urls = min(len(urls), 20)
    added = 0

    for idx, url in enumerate(urls[:max_urls]):
        print(f"   [{idx + 1}/{max_urls}] {url[:50]}...")

        # 각 URL 추가 전 오버레이 정리
        if idx > 0:
            await _clear_overlays(page)
            await page.wait_for_timeout(2000)

        success = await _add_single_url(page, url)
        if success:
            added += 1
        else:
            print(f"   ⚠️ URL {idx + 1} 추가 실패")
            await _screenshot(page, f"err_url_{idx}")
            await _clear_overlays(page)
            await page.wait_for_timeout(2000)

    # 소스 처리 대기 (URL 추가 후 인덱싱 시간)
    if added > 0:
        print(f"   ⏳ {added}개 소스 처리 대기 중 (30초)...")
        await page.wait_for_timeout(30000)

    return added


# ─────────────────────────────────────────────────────────────
# Step 4: 비디오 생성 + 다운로드
# ─────────────────────────────────────────────────────────────

async def _click_studio_card(page, card_text: str) -> bool:
    """Studio 패널의 특정 카드를 클릭하여 생성 패널 열기

    전략:
    1. 텍스트 라벨을 가진 가장 작은 요소를 정확히 찾기
    2. 해당 라벨에서 최대 3단계 부모까지만 올라가 카드 컨테이너 식별
       (너무 높이 올라가면 전체 패널을 카드로 오인)
    3. 카드 컨테이너 내 연필 아이콘 버튼 클릭 → 없으면 카드 자체 클릭
    """
    result = await page.evaluate(f"""
        (() => {{
            const text = {json_module.dumps(card_text)};

            // 1. 텍스트를 직접 포함하는 가장 작은 요소 찾기
            let bestLabel = null;
            let bestArea = Infinity;

            const allEls = document.querySelectorAll('span, div, p, h3, h4, a');
            for (const el of allEls) {{
                if (el.offsetParent === null) continue;

                // 직접 텍스트 노드만 확인 (자식 요소 텍스트 제외)
                const directText = Array.from(el.childNodes)
                    .filter(n => n.nodeType === 3)
                    .map(n => n.textContent.trim())
                    .join('');

                if (!directText.includes(text)) continue;

                const rect = el.getBoundingClientRect();
                const area = rect.width * rect.height;
                if (area < 10) continue;

                if (area < bestArea) {{
                    bestLabel = el;
                    bestArea = area;
                }}
            }}

            if (!bestLabel) return null;

            // 2. 부모 체인에서 카드 컨테이너 찾기 (최대 3단계만!)
            //    "panel-content-scrollable" 같은 큰 컨테이너까지 올라가면 안 됨
            let card = bestLabel;
            let parent = bestLabel.parentElement;
            for (let i = 0; i < 3 && parent; i++) {{
                const rect = parent.getBoundingClientRect();
                const area = rect.width * rect.height;

                // 너무 큰 요소 (패널 전체)는 카드가 아님
                if (area > 50000) break;

                // 카드 크기 범위 (대략 100x60 ~ 200x100)
                if (rect.width > 80 && rect.width < 300 && rect.height > 40 && rect.height < 200) {{
                    card = parent;
                }}
                parent = parent.parentElement;
            }}

            // 3. 카드 내 버튼 찾기 (연필 아이콘)
            const btns = card.querySelectorAll('button, [role="button"]');
            for (const btn of btns) {{
                const matIcon = btn.querySelector('mat-icon, .material-icons, svg, img');
                if (matIcon) {{
                    btn.click();
                    const labelRect = bestLabel.getBoundingClientRect();
                    const cardRect = card.getBoundingClientRect();
                    return 'pencil-btn in ' + card.tagName +
                           '(card:' + Math.round(cardRect.width) + 'x' + Math.round(cardRect.height) +
                           ', label:' + bestLabel.innerText.trim().substring(0, 20) + ')';
                }}
            }}

            // 4. 버튼 없으면 카드 자체 클릭
            card.click();
            const cardRect = card.getBoundingClientRect();
            return 'card-click: ' + card.tagName +
                   '(' + Math.round(cardRect.width) + 'x' + Math.round(cardRect.height) +
                   '): ' + bestLabel.innerText.trim().substring(0, 20);
        }})()
    """)
    if result:
        print(f"   Studio 카드 클릭: {result[:80]}")
        return True
    return False


async def _generate_and_download_video(page, output_path: str) -> Optional[str]:
    """동영상 개요 → 생성 → 다운로드"""

    # 1. 오버레이 정리 + 소스 처리 대기
    await _clear_overlays(page)
    print("   소스 처리 대기 중 (8초)...")
    await page.wait_for_timeout(8000)
    await _screenshot(page, "step4_before_video")

    # 2. "동영상 개요" 카드 클릭 (3가지 전략)
    await _clear_overlays(page)
    print("   '동영상 개요' 클릭 중...")

    clicked = False

    # 전략 A: Studio 카드 전용 클릭 (연필 아이콘 → 카드 컨테이너)
    clicked = await _click_studio_card(page, "동영상 개요")
    if not clicked:
        clicked = await _click_studio_card(page, "Video Overview")

    if not clicked:
        # 전략 B: 일반 JS 클릭 (부모 카드 찾기)
        clicked = await _js_find_and_click_specific(page, "동영상 개요")
    if not clicked:
        clicked = await _js_find_and_click_specific(page, "Video Overview")

    if not clicked:
        # 전략 C: Playwright 셀렉터 force 클릭
        for sel in [
            "text='동영상 개요'",
            "button:has-text('동영상 개요')",
            "[role='button']:has-text('동영상 개요')",
        ]:
            try:
                elem = page.locator(sel).first
                if await elem.is_visible(timeout=3000):
                    await elem.click(force=True)
                    clicked = True
                    print(f"   Playwright force click: {sel}")
                    break
            except Exception:
                continue

    if clicked:
        print("   ✅ '동영상 개요' 클릭")
    else:
        await _screenshot(page, "err_video_overview")
        print("   ⚠️ '동영상 개요' 클릭 실패")

    await page.wait_for_timeout(5000)  # 카드 활성화 → 맞춤설정 모달 표시 대기
    await _screenshot(page, "step4_after_card_click")

    # 3. "생성" 버튼 찾기 (최대 20초 대기)
    # ⚠️ _clear_overlays() 호출하면 Escape로 모달이 닫히므로 호출하지 않음!
    print("   '생성' 버튼 찾는 중...")

    gen_clicked = False

    for wait_round in range(7):
        # JS로 "생성" 버튼 찾기 - 정확한 텍스트 매칭
        # "생성 중..." 같은 진행 상태 텍스트가 아닌, 정확히 "생성"인 버튼만 클릭
        gen_result = await page.evaluate("""
            (() => {
                const btns = document.querySelectorAll('button');
                for (const btn of btns) {
                    if (btn.offsetParent === null) continue;
                    const txt = (btn.innerText || '').trim();
                    // 정확히 "생성" 또는 "Generate"만 매칭 (길이 제한으로 "생성 중..." 제외)
                    if (txt === '생성' || txt === 'Generate' ||
                        txt === '생성하기' || txt === '만들기') {
                        btn.click();
                        return 'exact: ' + txt;
                    }
                }
                // 폴백: "생성" 포함하되 "중" 미포함 (진행 상태 제외)
                for (const btn of btns) {
                    if (btn.offsetParent === null) continue;
                    const txt = (btn.innerText || '').trim();
                    if ((txt.includes('생성') || txt.includes('Generate')) &&
                        !txt.includes('중') && !txt.includes('ing') &&
                        txt.length < 15) {
                        btn.click();
                        return 'partial: ' + txt;
                    }
                }
                return null;
            })()
        """)
        if gen_result:
            print(f"   JS 생성 버튼: {gen_result}")
            gen_clicked = True
            break

        # 못 찾으면 3초 더 대기
        if wait_round < 6:
            await page.wait_for_timeout(3000)

    if not gen_clicked:
        await _screenshot(page, "err_generate_btn")
        print("   ❌ 생성 버튼 없음")

        # 디버그: DOM에서 모든 보이는 버튼의 텍스트 덤프
        btn_dump = await page.evaluate("""
            (() => {
                const btns = document.querySelectorAll('button');
                return Array.from(btns)
                    .filter(b => b.offsetParent !== null)
                    .map(b => {
                        const txt = b.innerText.trim().substring(0, 40);
                        const rect = b.getBoundingClientRect();
                        return txt + '(' + Math.round(rect.width) + 'x' + Math.round(rect.height) + ')';
                    })
                    .filter(t => t.length > 3)
                    .join(' | ');
            })()
        """)
        print(f"   현재 보이는 버튼: {btn_dump[:300]}")
        return None

    print(f"   ✅ 생성 클릭! ⏳ 비디오 생성 중 (최대 {MAX_WAIT_MINUTES}분)...")

    # 4. 비디오 완료 감지 + 다운로드 폴링
    total_checks = MAX_WAIT_MINUTES * 4  # 15초 간격
    for i in range(total_checks):
        # asyncio.sleep 사용 (page.wait_for_timeout은 브라우저 연결에 의존)
        await asyncio.sleep(15)
        # keepalive: 페이지가 살아있는지 확인
        try:
            await page.evaluate("1+1")
        except Exception:
            print(f"\n   ⚠️ 브라우저 닫힘")
            return None

        elapsed = (i + 1) * 15
        m, s = divmod(elapsed, 60)
        print(f"   ⏳ {m}분 {s}초 경과... ({i+1}/{total_checks})", end="\r")

        # 3분마다 스크린샷
        if elapsed % 180 == 0:
            try:
                await _screenshot(page, f"progress_{m}min")
            except Exception:
                pass

        # 비디오 완료 감지 (2가지 방법)
        try:
            video_status = await page.evaluate("""
                (() => {
                    // 방법 1: 직접 "다운로드" 버튼 탐색
                    const btns = document.querySelectorAll('button, [role="button"]');
                    for (const b of btns) {
                        const txt = (b.innerText || '').trim();
                        const label = b.getAttribute('aria-label') || '';
                        if (txt.includes('다운로드') || txt.includes('Download') ||
                            label.includes('다운로드') || label.includes('Download video')) {
                            return 'download_btn_visible';
                        }
                    }

                    // 방법 2: Studio 패널에서 "동영상" 또는 "설명 동영상" 항목에 ▶ 재생 버튼 존재 확인
                    // 완료된 비디오는 "설명 동영상 · 소스 N개 · X분 전" 형태로 표시됨
                    const allEls = document.querySelectorAll('*');
                    for (const el of allEls) {
                        const txt = (el.innerText || '').trim();
                        if ((txt.includes('설명 동영상') || txt.includes('요약 동영상') ||
                             txt.includes('Explanatory video') || txt.includes('Summary video')) &&
                            (txt.includes('분 전') || txt.includes('min ago') ||
                             txt.includes('초 전') || txt.includes('sec ago') ||
                             txt.includes('방금') || txt.includes('just now'))) {
                            return 'video_completed';
                        }
                    }

                    // 방법 3: "동영상 개요 생성 중" 텍스트가 여전히 있으면 아직 진행 중
                    for (const el of allEls) {
                        const txt = (el.innerText || '').trim();
                        if (txt.includes('동영상 개요 생성 중') || txt.includes('Video overview generating')) {
                            return 'still_generating';
                        }
                    }

                    return 'unknown';
                })()
            """)

            if video_status == 'download_btn_visible':
                # 다운로드 버튼이 직접 보임
                print(f"\n   ✅ 생성 완료! ({m}분 {s}초 소요)")
                return await _download_video(page, output_path)

            elif video_status == 'video_completed':
                # 비디오 완료됨 → ⋮ 메뉴에서 다운로드 찾기
                print(f"\n   ✅ 비디오 생성 완료 감지! ({m}분 {s}초 소요)")
                await _screenshot(page, "video_completed")
                return await _download_from_menu(page, output_path)

        except Exception as e:
            if "closed" in str(e).lower() or "target" in str(e).lower():
                print(f"\n   ⚠️ 페이지 닫힘")
                return None
            continue

    print(f"\n   ⚠️ {MAX_WAIT_MINUTES}분 초과")
    try:
        await _screenshot(page, "err_timeout")
    except Exception:
        pass
    return None


async def _download_video(page, output_path: str) -> Optional[str]:
    """직접 보이는 다운로드 버튼으로 다운로드"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    dl_btn = await _find_button(page, [
        "button:has-text('다운로드')",
        "button:has-text('Download')",
        "[aria-label*='다운로드']",
        "[aria-label*='Download']",
    ], timeout=5000)

    if dl_btn:
        try:
            async with page.expect_download(timeout=60000) as dl_info:
                await dl_btn.click()
            dl = await dl_info.value
            await dl.save_as(output_path)
            print(f"   📥 다운로드 완료: {output_path}")
            return output_path
        except Exception as e:
            print(f"   ⚠️ 다운로드 오류: {e}")

    # JS 클릭 폴백
    await _js_find_and_click(page, "다운로드")
    await page.wait_for_timeout(10000)
    return output_path


async def _download_from_menu(page, output_path: str) -> Optional[str]:
    """비디오 항목의 ⋮ 메뉴 또는 플레이어에서 다운로드"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # 전략 1: 비디오 항목의 ▶ 버튼을 클릭 → 플레이어 열기 → 플레이어 ... 메뉴에서 다운로드
    # (⋮ 메뉴 타겟팅이 어려우므로 플레이어 우선)
    print("   ▶️ 비디오 플레이어 열기...")
    play_clicked = await page.evaluate("""
        (() => {
            // Studio 패널(우측)에서 비디오 항목의 ▶ 재생 버튼 찾기
            // 비디오 항목: "설명 동영상" 텍스트 포함하는 행 내의 play 버튼
            const allBtns = document.querySelectorAll('button');
            for (const btn of allBtns) {
                const rect = btn.getBoundingClientRect();
                if (rect.x < 800 || btn.offsetParent === null) continue;

                const icon = btn.querySelector('mat-icon, .material-icons');
                const iconTxt = (icon?.innerText || '').trim();
                const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();

                if (iconTxt === 'play_arrow' || iconTxt === 'play_circle' ||
                    ariaLabel.includes('play') || ariaLabel.includes('재생')) {
                    // 이 버튼이 비디오 항목(설명 동영상) 근처인지 확인
                    let parent = btn.parentElement;
                    for (let i = 0; i < 4 && parent; i++) {
                        const txt = (parent.innerText || '').trim();
                        if (txt.includes('설명 동영상') || txt.includes('요약 동영상') ||
                            txt.includes('Explanatory') || txt.includes('Summary video')) {
                            btn.click();
                            return 'play at x=' + Math.round(rect.x) + ',y=' + Math.round(rect.y);
                        }
                        parent = parent.parentElement;
                    }
                }
            }
            // 폴백: Studio 패널의 아무 play 버튼
            for (const btn of allBtns) {
                const rect = btn.getBoundingClientRect();
                if (rect.x < 800 || btn.offsetParent === null) continue;
                const icon = btn.querySelector('mat-icon, .material-icons');
                const iconTxt = (icon?.innerText || '').trim();
                if (iconTxt === 'play_arrow' || iconTxt === 'play_circle') {
                    btn.click();
                    return 'play-fallback at x=' + Math.round(rect.x);
                }
            }
            return null;
        })()
    """)

    if play_clicked:
        print(f"   ▶️ 플레이어 클릭: {play_clicked}")
        await page.wait_for_timeout(5000)
        await _screenshot(page, "video_player_open")

        # 플레이어 상단의 ... (more_horiz) 메뉴 클릭
        # 플레이어 헤더: "어린 왕자: ..." 제목 + 공유 아이콘 + ... 아이콘
        # ... 아이콘은 플레이어 헤더 우측 상단 (y < 200, x > 1100)
        player_menu = await page.evaluate("""
            (() => {
                const btns = document.querySelectorAll('button');
                // 플레이어 헤더 영역의 ... 버튼 (y < 200, x > 1100)
                let candidates = [];
                for (const btn of btns) {
                    const rect = btn.getBoundingClientRect();
                    if (rect.x < 1100 || rect.y > 200) continue;
                    if (btn.offsetParent === null) continue;

                    const icon = btn.querySelector('mat-icon, .material-icons');
                    const iconTxt = (icon?.innerText || '').trim();
                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();

                    if (iconTxt === 'more_horiz' || iconTxt === 'more_vert' ||
                        iconTxt === '...' || iconTxt === '⋯' ||
                        ariaLabel.includes('more') || ariaLabel.includes('option') ||
                        ariaLabel.includes('menu') || ariaLabel.includes('더보기')) {
                        candidates.push({btn, x: rect.x, y: rect.y, icon: iconTxt, label: ariaLabel});
                    }
                }
                // 가장 우측 상단의 버튼 선택
                if (candidates.length > 0) {
                    candidates.sort((a, b) => b.x - a.x);
                    candidates[0].btn.click();
                    return 'menu at x=' + Math.round(candidates[0].x) + ',y=' + Math.round(candidates[0].y) +
                           ' icon=' + candidates[0].icon;
                }
                return null;
            })()
        """)

        if player_menu:
            print(f"   플레이어 메뉴: {player_menu}")
            await page.wait_for_timeout(2000)
            await _screenshot(page, "player_menu_open")

            dl_result = await _click_menu_download(page, output_path)
            if dl_result:
                return dl_result
        else:
            print("   ❌ 플레이어 ... 메뉴 못 찾음")
    else:
        print("   ❌ ▶️ 재생 버튼 못 찾음")

    # 전략 2: Studio 패널의 비디오 항목 ⋮ 메뉴 직접 클릭 (x > 1150)
    print("   💡 Studio 패널 ⋮ 메뉴 시도...")
    menu_clicked = await page.evaluate("""
        (() => {
            const btns = document.querySelectorAll('button');
            for (const btn of btns) {
                const rect = btn.getBoundingClientRect();
                // Studio 패널 우측 끝 (x > 1150, 채팅 ⋮는 x~850)
                if (rect.x < 1150 || btn.offsetParent === null) continue;

                const icon = btn.querySelector('mat-icon, .material-icons');
                const iconTxt = (icon?.innerText || '').trim();

                if (iconTxt === 'more_vert') {
                    // 비디오 항목 근처인지 확인
                    let p = btn.parentElement;
                    for (let i = 0; i < 5 && p; i++) {
                        const txt = (p.innerText || '');
                        if (txt.includes('설명 동영상') || txt.includes('요약 동영상')) {
                            btn.click();
                            return 'video-⋮ at x=' + Math.round(rect.x) + ',y=' + Math.round(rect.y);
                        }
                        p = p.parentElement;
                    }
                }
            }
            return null;
        })()
    """)

    if menu_clicked:
        print(f"   ⋮ 메뉴: {menu_clicked}")
        await page.wait_for_timeout(2000)
        await _screenshot(page, "studio_menu_open")

        dl_result = await _click_menu_download(page, output_path)
        if dl_result:
            return dl_result

    await _screenshot(page, "err_download_all_failed")
    print("   ❌ 모든 다운로드 방법 실패")
    return None


async def _click_menu_download(page, output_path: str) -> Optional[str]:
    """열린 메뉴(오버레이)에서 다운로드 클릭 + 파일 저장"""
    # 오버레이/메뉴에서 다운로드 항목 찾기
    dl_clicked = await page.evaluate("""
        (() => {
            // CDK 오버레이 메뉴 아이템
            const selectors = [
                '.cdk-overlay-pane button',
                '.cdk-overlay-pane [role="menuitem"]',
                '.mat-menu-content button',
                '[role="menu"] button',
                '[role="menu"] [role="menuitem"]',
                '.cdk-overlay-pane a',
            ];
            for (const sel of selectors) {
                const items = document.querySelectorAll(sel);
                for (const item of items) {
                    const txt = (item.innerText || '').trim();
                    if (txt.includes('다운로드') || txt.includes('Download')) {
                        item.click();
                        return 'download: ' + txt;
                    }
                }
            }
            // 폴백: 전체 보이는 요소
            const all = document.querySelectorAll('button, [role="menuitem"], a');
            for (const el of all) {
                if (el.offsetParent === null) continue;
                const txt = (el.innerText || '').trim();
                if (txt.includes('다운로드') || txt.includes('Download')) {
                    el.click();
                    return 'fallback: ' + txt;
                }
            }

            // 디버그: 메뉴 내용 덤프
            const overlayItems = document.querySelectorAll('.cdk-overlay-pane *');
            const texts = [];
            for (const item of overlayItems) {
                const t = (item.innerText || '').trim();
                if (t && t.length < 30 && !texts.includes(t)) texts.push(t);
            }
            return 'NO_DOWNLOAD_FOUND|menu:' + texts.join(',');
        })()
    """)

    if dl_clicked and not dl_clicked.startswith('NO_DOWNLOAD'):
        print(f"   메뉴 다운로드: {dl_clicked}")
        try:
            async with page.expect_download(timeout=60000) as dl_info:
                await page.wait_for_timeout(1000)
            dl = await dl_info.value
            await dl.save_as(output_path)
            print(f"   📥 다운로드 완료: {output_path}")
            return output_path
        except Exception as e:
            print(f"   ⚠️ 다운로드 대기 오류: {e}")
    else:
        menu_content = dl_clicked.split('|')[-1] if dl_clicked else 'empty'
        print(f"   ❌ 메뉴에 다운로드 없음 ({menu_content[:80]})")
        await _screenshot(page, "err_menu_no_download")

    return None


# ─────────────────────────────────────────────────────────────
# 메인 흐름
# ─────────────────────────────────────────────────────────────

async def create_notebooklm_video(
    book_title: str,
    language: str,
    urls: list[str],
    output_path: str,
    headless: bool = False,
    notebook_url: Optional[str] = None,
) -> Optional[str]:
    """NotebookLM Video Overview 자동 생성 및 다운로드"""
    from playwright.async_api import async_playwright

    if not SESSION_FILE.exists():
        print("❌ 로그인 세션이 없습니다. 먼저 --login 옵션으로 로그인하세요.")
        return None

    lang_label = "KR" if language == "ko" else "EN"
    print(f"\n📖 NotebookLM 비디오 생성 시작")
    print(f"   노트북: {book_title} [{lang_label}]")
    print(f"   소스 URL: {len(urls)}개")
    print(f"   출력: {output_path}")
    if notebook_url:
        print(f"   기존 노트북: {notebook_url}")

    PROFILE_DIR = DEFAULT_PROFILE_DIR
    PROFILE_DIR.mkdir(exist_ok=True)

    # Seed profile with session cookies on first use
    if SESSION_FILE.exists() and not (PROFILE_DIR / ".seeded").exists():
        import json as _json
        seed_state = _json.loads(SESSION_FILE.read_text())
        seed_path = PROFILE_DIR / "seed_state.json"
        seed_path.write_text(_json.dumps(seed_state))
        (PROFILE_DIR / ".seeded").touch()

    async with async_playwright() as p:
        # Use persistent context so Google session cookies survive across runs
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            accept_downloads=True,
            args=[
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
            ],
        )
        # Inject cookies from session file if profile is fresh (first run)
        seed_path = PROFILE_DIR / "seed_state.json"
        if seed_path.exists():
            import json as _json
            seed = _json.loads(seed_path.read_text())
            await context.add_cookies(seed.get("cookies", []))
            seed_path.unlink()

        page = await context.new_page()

        try:
            # ── 기존 노트북 재사용 모드 ──
            if notebook_url:
                print("\n♻️  기존 노트북으로 이동...")
                await page.goto(notebook_url, wait_until="load", timeout=60000)
                await page.wait_for_timeout(5000)

                # 세션 만료 체크
                if "accounts.google.com" in page.url or "signin" in page.url:
                    print("❌ 세션 만료. --login 으로 재로그인하세요.")
                    return None

                # 바로 비디오 생성/다운로드 단계로
                print("\n4️⃣  Video Overview 생성/다운로드...")
                video_path = await _generate_and_download_video(page, output_path)

                if video_path:
                    print(f"\n✅ 비디오 완료: {video_path}")
                    _notify(f"'{book_title}' 비디오 완료!", success=True)
                else:
                    _notify(f"'{book_title}' 비디오 실패", success=False)
                return video_path

            # ── 새 노트북 생성 모드 ──

            # Step 1: 접속
            print("\n1️⃣  NotebookLM 접속...")
            await page.goto(NOTEBOOKLM_URL, wait_until="load", timeout=60000)

            # 무음 SSO 바운스(accounts.google.com 경유 후 복귀) 대기 — 즉시 판정 금지
            for _ in range(10):
                if "accounts.google.com" not in page.url:
                    break
                await page.wait_for_timeout(2000)

            if "accounts.google.com" in page.url:
                await _screenshot(page, "session_expired")
                print("❌ 세션 만료. --login 으로 재로그인하세요.")
                return None

            await _wait_for_page_ready(page, timeout_ms=60000)

            # Step 2: 새 노트북
            print("\n2️⃣  새 노트북 생성...")
            if not await _click_new_notebook(page):
                return None

            await page.wait_for_timeout(5000)
            await _screenshot(page, "after_new_notebook_click")
            print(f"   🔗 현재 URL: {page.url}")

            # 노트북 URL 저장 (resume 지원)
            current_url = page.url
            _save_notebook_url(book_title, current_url)
            print(f"   📎 노트북 URL 저장: {current_url[:60]}...")

            # Step 3: 소스 추가
            print(f"\n3️⃣  소스 URL {len(urls)}개 추가...")
            added = await _add_sources(page, urls)
            if added == 0:
                print("❌ 소스 추가 실패")
                return None
            print(f"   ✅ {added}개 소스 추가 완료")
            await page.wait_for_timeout(5000)

            # Step 4: 비디오 생성
            print("\n4️⃣  Video Overview 생성...")
            video_path = await _generate_and_download_video(page, output_path)

            if video_path:
                print(f"\n✅ 비디오 완료: {video_path}")
                _notify(f"'{book_title}' 비디오 완료!", success=True)
            else:
                print("\n❌ 비디오 실패")
                print(f"   💡 재시도: python scripts/notebooklm_automator.py --book-title \"{book_title}\" --notebook-url \"{current_url}\"")
                _notify(f"'{book_title}' 비디오 실패", success=False)

            return video_path

        except Exception as e:
            print(f"❌ 오류: {e}")
            try:
                await _screenshot(page, "err_fatal")
            except Exception:
                pass
            _notify(f"오류: {str(e)[:50]}", success=False)
            raise
        finally:
            try:
                await context.close()
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def generate_video_for_book(
    book_title: str,
    language: str,
    urls_file: Optional[str] = None,
    urls: Optional[list] = None,
    output_dir: str = "input",
    headless: bool = False,
    notebook_url: Optional[str] = None,
) -> Optional[str]:
    """동기 래퍼"""
    if not SESSION_FILE.exists():
        print("❌ 세션 없음. python scripts/notebooklm_automator.py --login")
        return None

    if urls is None and notebook_url is None:
        if urls_file and Path(urls_file).exists():
            urls = extract_urls_from_md(urls_file)
        else:
            print("❌ URL 파일 없음:", urls_file)
            return None

    if not urls and not notebook_url:
        print("❌ URL 없음")
        return None

    urls = urls or []
    lang_suffix = "kr" if language == "ko" else "en"
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in book_title)
    output_path = str(Path(output_dir) / f"{safe_title}_video_{lang_suffix}.mp4")

    return asyncio.run(
        create_notebooklm_video(
            book_title=book_title,
            language=language,
            urls=urls,
            output_path=output_path,
            headless=headless,
            notebook_url=notebook_url,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="NotebookLM Video Overview 자동화")
    parser.add_argument("--login", action="store_true", help="Google 로그인 세션 생성")
    parser.add_argument("--book-title", help="책 제목")
    parser.add_argument("--language", choices=["ko", "en"], default="ko")
    parser.add_argument("--urls-file", help="URL 목록 MD 파일")
    parser.add_argument("--output-dir", default="input")
    parser.add_argument("--headless", action="store_true", help="헤드리스 모드")
    parser.add_argument("--notebook-url", help="기존 노트북 URL (resume)")
    args = parser.parse_args()

    if args.login:
        login(headless=args.headless)
        return

    if not args.book_title:
        parser.error("--book-title 필요")

    # 저장된 노트북 URL 확인 (notebook_url 미지정 시)
    notebook_url = args.notebook_url
    if not notebook_url and not args.urls_file:
        saved_url = _load_notebook_url(args.book_title)
        if saved_url:
            print(f"💡 저장된 노트북 발견: {saved_url[:60]}...")
            notebook_url = saved_url

    result = generate_video_for_book(
        book_title=args.book_title,
        language=args.language,
        urls_file=args.urls_file,
        output_dir=args.output_dir,
        headless=args.headless,
        notebook_url=notebook_url,
    )

    if result:
        print(f"\n✅ 완료: {result}")
    else:
        print("\n❌ 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
