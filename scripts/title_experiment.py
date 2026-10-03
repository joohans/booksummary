#!/usr/bin/env python3
"""제목 실험 — 제목에 「줄거리·해설」을 넣으면 「책 제목 + 줄거리」 검색을 더 받는가.

설계(2026-10-03):
  - 대상: 공개된 「핵심 요약」 소설 편 중 네이버 「<책> 줄거리」 수요가 월 90회 이상인 7편.
    새 선정 기준 9편·경쟁 실험 3편은 12월 선정 기준 판정을 오염시키지 않도록 제외했다.
  - 짝: 비슷한 검색 유입·같은 제목 형식끼리 3쌍 + 남는 1편은 대조군.
    짝 안에서 무작위(seed 고정)로 한쪽만 제목을 바꾼다.
  - 지표: ① 검색 유입 조회(YT_SEARCH) ② 그 영상에 들어온 검색어 중 「줄거리」 포함 조회.
    사전 28일(9/03~9/30) 대 사후 28일(적용 다음 날부터)의 이중차분.
  - 원복: rollback 하면 저장해 둔 원래 제목으로 되돌린다.

사용법:
  title_experiment.py plan            # 배정과 바뀔 제목 미리보기(변경 없음)
  title_experiment.py apply           # 사전 지표 저장 + 처치군 제목 변경
  title_experiment.py measure         # 사후 지표 측정·비교(적용 후 31일 이상 지나서)
  title_experiment.py rollback        # 처치군 제목 원복
"""
import json
import random
import sys
import time
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily_pulse as dp  # noqa: E402  (OAuth 클라이언트·조회 함수 재사용)

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "data" / "title_experiment.json"
SEED = 20261003
PRE = ("2026-09-03", "2026-09-30")

# (짝 이름, [(videoId, 책 제목, 네이버 「책 줄거리」 월간 수요)])
PAIRS = [
    ("A", [("sV-qZxxjR0g", "종의 기원", 370), ("yRAkdoT_cXA", "살인자의 기억법", 190)]),
    ("B", [("L8FLJWGj7GE", "인간 실격", 1010), ("K8MIWCe30D8", "노인과 바다", 1930)]),
    ("C", [("BnovpY5w5ZM", "이반 일리치의 죽음", 110), ("iZ9rOZbLxxM", "멋진 신세계", 260)]),
]
EXTRA_CONTROL = [("8r4Mn3Vxdc8", "미드나잇 라이브러리", 90)]
SUFFIX = " 줄거리·해설"


def assign():
    rng = random.Random(SEED)
    treat, ctrl = [], []
    for name, pair in PAIRS:
        t = rng.randrange(2)
        treat.append((name,) + pair[t])
        ctrl.append((name,) + pair[1 - t])
    ctrl += [("-",) + x for x in EXTRA_CONTROL]
    return treat, ctrl


def new_title(title, book):
    if "줄거리" in title:
        return title
    i = title.find(book)
    if i < 0:
        raise SystemExit(f"제목에서 책 이름을 못 찾음: {book} / {title}")
    j = i + len(book)
    if title[j:].startswith(" 핵심 정리"):  # 옛 형식: 「X 핵심 정리 | [Summary] …」
        t = title[:j] + " 줄거리·핵심 정리" + title[j + len(" 핵심 정리"):]
    else:
        t = title[:j] + SUFFIX + title[j:]
    if len(t) > 100:
        raise SystemExit(f"100자 초과: {t}")
    return t


def metrics(ya, vid, start, end):
    src = dict(dp.q(ya, startDate=start, endDate=end, metrics="views",
                    dimensions="insightTrafficSourceType", filters=f"video=={vid}"))
    terms = dp.q(ya, startDate=start, endDate=end, metrics="views",
                 dimensions="insightTrafficSourceDetail",
                 filters=f"video=={vid};insightTrafficSourceType==YT_SEARCH",
                 sort="-views", maxResults=25)
    plot = sum(v for k, v in terms if "줄거리" in k)
    return {"search": int(src.get("YT_SEARCH", 0)), "total": int(sum(src.values())),
            "plot_terms": int(plot), "top_terms": terms[:8]}


def get_snippet(yt, vid):
    v = yt.videos().list(part="snippet,localizations", id=vid).execute()["items"][0]
    return v["snippet"], v.get("localizations", {})


def set_title(yt, vid, title):
    sn, loc = get_snippet(yt, vid)
    body_sn = {"title": title, "description": sn["description"], "categoryId": sn["categoryId"],
               "tags": sn.get("tags", []), "defaultLanguage": sn.get("defaultLanguage", "ko")}
    body = {"id": vid, "snippet": body_sn}
    parts = "snippet"
    if loc:
        loc = dict(loc)
        if "ko" in loc:
            loc["ko"] = {**loc["ko"], "title": title}
        body["localizations"] = loc
        parts = "snippet,localizations"
    yt.videos().update(part=parts, body=body).execute()
    # 수정 직후 list 는 옛 제목을 돌려줄 때가 있다(2026-10-03 실측) → 최대 30초 재확인
    for _ in range(10):
        after, _ = get_snippet(yt, vid)
        if after["title"] == title:
            break
        time.sleep(3)
    assert after["title"] == title, after["title"]
    assert after.get("tags", []) == sn.get("tags", []), "태그가 바뀌었다"


def cmd_plan(yt):
    treat, ctrl = assign()
    print(f"seed={SEED}\n[처치군 — 제목 변경]")
    for name, vid, book, dem in treat:
        sn, _ = get_snippet(yt, vid)
        print(f"  {name} {book} (줄거리 수요 {dem})\n     전: {sn['title']}\n     후: {new_title(sn['title'], book)}")
    print("[대조군 — 그대로]")
    for name, vid, book, dem in ctrl:
        print(f"  {name} {book} (줄거리 수요 {dem})")


def cmd_apply(yt, ya):
    if STATE.exists():  # 중단된 적용 이어 하기 — 사전 지표는 다시 재지 않는다
        state = json.loads(STATE.read_text(encoding="utf-8"))
        for vid, v in state["videos"].items():
            if v["group"] == "treat" and "new_title" not in v:
                t = new_title(v["original_title"], v["book"])
                set_title(yt, vid, t)
                v["new_title"] = t
                print(f"✅ {v['book']}: {t}")
                STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"이어 적용 완료: {STATE}")
        return
    treat, ctrl = assign()
    today = dt.date.today().isoformat()
    state = {"seed": SEED, "applied": today, "pre": PRE, "videos": {}}
    for group, rows in (("treat", treat), ("control", ctrl)):
        for name, vid, book, dem in rows:
            sn, _ = get_snippet(yt, vid)
            state["videos"][vid] = {"group": group, "pair": name, "book": book, "plot_demand": dem,
                                    "original_title": sn["title"], "pre": metrics(ya, vid, *PRE)}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    for vid, v in state["videos"].items():
        if v["group"] == "treat":
            t = new_title(v["original_title"], v["book"])
            set_title(yt, vid, t)
            v["new_title"] = t
            print(f"✅ {v['book']}: {t}")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {STATE}")


def cmd_measure(ya):
    state = json.loads(STATE.read_text(encoding="utf-8"))
    start = dt.date.fromisoformat(state["applied"]) + dt.timedelta(days=1)
    end = start + dt.timedelta(days=27)
    if end > dt.date.today() - dt.timedelta(days=3):
        print(f"⚠️ 사후 28일({start}~{end})이 아직 안 찼다(Analytics 2~3일 지연). 지금 값은 부분 집계다")
    agg = {"treat": [0, 0, 0, 0], "control": [0, 0, 0, 0]}
    print(f"사전 {state['pre'][0]}~{state['pre'][1]} / 사후 {start}~{end}")
    for vid, v in state["videos"].items():
        post = metrics(ya, vid, str(start), str(end))
        v["post"] = post
        a = agg[v["group"]]
        a[0] += v["pre"]["search"]; a[1] += post["search"]
        a[2] += v["pre"]["plot_terms"]; a[3] += post["plot_terms"]
        print(f"  [{v['group']:7}] {v['book']:12} 검색 {v['pre']['search']:4}→{post['search']:4}"
              f"  줄거리검색어 {v['pre']['plot_terms']:3}→{post['plot_terms']:3}")
    for g, (s0, s1, p0, p1) in agg.items():
        r = (s1 / s0) if s0 else float("nan")
        print(f"  {g:7} 합계 검색 {s0}→{s1} (×{r:.2f}) · 줄거리검색어 {p0}→{p1}")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_rollback(yt):
    state = json.loads(STATE.read_text(encoding="utf-8"))
    for vid, v in state["videos"].items():
        if v["group"] == "treat":
            set_title(yt, vid, v["original_title"])
            print(f"↩️ {v['book']}: {v['original_title']}")
    state["rolled_back"] = dt.date.today().isoformat()
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    yt, ya = dp.clients()
    {"plan": lambda: cmd_plan(yt), "apply": lambda: cmd_apply(yt, ya),
     "measure": lambda: cmd_measure(ya), "rollback": lambda: cmd_rollback(yt)}[cmd]()


if __name__ == "__main__":
    main()
