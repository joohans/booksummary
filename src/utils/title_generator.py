#!/usr/bin/env python3
"""
인문학적 가치를 강조하는 제목 생성 유틸리티

AI 강조를 피하고 인문학적 호기심을 자극하는 제목을 생성합니다.
"""

from typing import Optional, Dict
import re


def generate_seo_subtitle(
    language: str,
    book_title: str,
    author: Optional[str] = None,
    book_info: Optional[Dict] = None,
    content_type: str = "summary_video",
) -> str:
    """
    제목의 괄호 '(부제목)'에 들어갈 SEO용 짧은 문구를 생성합니다.

    - language='ko' 또는 'en'
    - 반환값은 괄호 없이 "..." 형태의 짧은 문구입니다.
    - 영문(en)은 "완전 영어(한글 0)"만을 목표로 하며, 템플릿/출력에 한글을 포함하지 않습니다.
    - content_type:
      - "summary_video": Summary + Deep Dive (5분 핵심 요약 + AI 심층 분석)
      - "full_episode": 일당백 Style Deep Dive (배경지식 → 인포그래픽 → 책 분석)
    - book_info(선택): Google Books의 categories/description 등을 힌트로 장르 추정에 사용합니다.
    """

    # Beyond Page 채널 포맷을 먼저 반영한 "기본 부제"를 만들고,
    # summary_video는 장르 키워드를 덧붙여 SEO를 강화합니다.
    if content_type == "summary_video":
        # 실제 영상 길이는 12~15분(요약 5분 + NLM 심층 리뷰 8~11분)이므로
        # 제목에 "5분"을 쓰면 5:00 부근 이탈을 유발한다 (2026-08-22 정리).
        # 앞에 붙는 "[핵심 요약]" 접두사와도 중복이므로 부제에서는 제외한다.
        base_ko = "AI 심층 분석"
        base_en = "AI Deep Dive"
    else:  # full_episode (일당백)
        base_ko = "배경지식·인포그래픽·책 분석"
        base_en = "Background · Infographics · Analysis"

        # 일당백은 구조가 고정이라 장르 키워드보다 구조 키워드를 우선합니다.
        return base_ko if language == "ko" else base_en

    # 장르별 키워드 접미(예: "· 핵심 주제·인사이트·정리")는 2026-08-22에 제거했다.
    # 제목이 70~87자까지 늘어나 모바일에서 잘렸고, 앞의 "[핵심 요약]" 접두사와
    # 의미가 겹쳐 실익이 없었다. 부제는 구조 설명만 담는다.
    return base_ko if language == "ko" else base_en


def generate_hashtags(
    language: str,
    book_title: str,
    author: Optional[str] = None,
    book_info: Optional[Dict] = None,
    content_type: str = "summary_video",
) -> str:
    """
    장르에 맞는 해시태그 문자열 생성

    Args:
        language: 'ko' 또는 'en'
        book_title: 책 제목
        author: 저자 이름 (선택)
        book_info: Google Books 정보 딕셔너리 (선택)
        content_type: 'summary_video' 또는 'full_episode'

    Returns:
        해시태그 문자열 (예: "#책리뷰 #BookSummary #자기계발")
    """

    def _category_text_for_hashtag() -> str:
        if not book_info:
            return ""
        cats = book_info.get("categories") or []
        if isinstance(cats, str):
            cats = [cats]
        cat_str = " ".join([c for c in cats if isinstance(c, str)])
        desc = book_info.get("description") if isinstance(book_info.get("description"), str) else ""
        return f"{cat_str}\n{desc}".lower()

    def _guess_genre_for_hashtag() -> str:
        text = _category_text_for_hashtag()
        title_lower = (book_title or "").lower()
        if "아포리즘" in (book_title or "") or "aphorism" in title_lower:
            return "philosophy"
        if any(k in text for k in ["philosophy", "철학"]):
            return "philosophy"
        if any(k in text for k in ["psychology", "self-help", "self help", "자기계발", "심리"]):
            return "psychology"
        if any(k in text for k in ["business", "economics", "management", "경제", "경영"]):
            return "business"
        if any(k in text for k in ["history", "역사"]):
            return "history"
        if any(k in text for k in ["science", "과학"]):
            return "science"
        if any(k in text for k in ["poetry", "시"]):
            return "poetry"
        if any(k in text for k in ["essay", "수필", "에세이"]):
            return "essay"
        if any(k in text for k in ["fiction", "novel", "소설"]):
            return "fiction"
        return "general"

    genre = _guess_genre_for_hashtag()

    # 공통 기본 해시태그
    if content_type == "full_episode":
        if language == "ko":
            base_tags = ["#책리뷰", "#북튜브", "#독서", "#BookReview"]
        else:
            base_tags = ["#BookReview", "#BookTube", "#Reading", "#책리뷰"]
    else:
        if language == "ko":
            base_tags = ["#핵심요약", "#책리뷰", "#북튜브"]
        else:
            base_tags = ["#BookSummary", "#BookReview", "#BookTube"]

    # 장르별 추가 해시태그
    genre_tags_ko = {
        "philosophy": ["#철학", "#인문학", "#삶의지혜"],
        "psychology": ["#심리학", "#자기계발", "#멘탈관리"],
        "business": ["#경영", "#경제", "#자기계발"],
        "history": ["#역사", "#인문학", "#교양"],
        "science": ["#과학", "#교양", "#지식"],
        "poetry": ["#시", "#문학", "#감성"],
        "essay": ["#에세이", "#수필", "#감성독서"],
        "fiction": ["#소설", "#문학", "#스토리"],
        "general": ["#독서", "#책추천", "#지식창고"],
    }
    genre_tags_en = {
        "philosophy": ["#Philosophy", "#Wisdom", "#Humanities"],
        "psychology": ["#Psychology", "#SelfHelp", "#Mindset"],
        "business": ["#Business", "#Economics", "#SelfHelp"],
        "history": ["#History", "#Humanities", "#Learning"],
        "science": ["#Science", "#Knowledge", "#Learning"],
        "poetry": ["#Poetry", "#Literature", "#Emotions"],
        "essay": ["#Essay", "#Literature", "#Reflection"],
        "fiction": ["#Fiction", "#Novel", "#Literature"],
        "general": ["#Reading", "#BookRecommendation", "#Knowledge"],
    }

    if language == "ko":
        extra = genre_tags_ko.get(genre, genre_tags_ko["general"])
    else:
        extra = genre_tags_en.get(genre, genre_tags_en["general"])

    all_tags = base_tags + extra
    return " ".join(all_tags)


def generate_engaging_title(
    book_title: str,
    author: Optional[str] = None,
    language: str = "ko",
    book_info: Optional[Dict] = None
) -> str:
    """
    인문학적 가치를 강조하는 제목 생성
    
    AI 강조를 피하고 인문학적 호기심을 자극하는 제목을 생성합니다.
    
    Args:
        book_title: 책 제목
        author: 저자 이름
        language: 언어 ('ko' 또는 'en')
        book_info: 책 정보 딕셔너리 (선택사항)
        
    Returns:
        생성된 제목
    """
    from src.utils.translations import (
        translate_book_title,
        translate_book_title_to_korean,
        translate_author_name,
        is_english_title
    )
    
    # 책 제목 번역
    if language == "ko":
        if is_english_title(book_title):
            ko_title = translate_book_title_to_korean(book_title)
        else:
            ko_title = book_title
        
        # 작가 이름 번역
        author_ko = ""
        if author:
            if is_english_title(author):
                author_ko = translate_author_name(author)
            else:
                author_ko = author
        
        # 인문학적 가치를 강조하는 제목 패턴 생성
        # 예: "조지 오웰이 경고한 미래가 현실이 되었다 (1984 깊이 읽기)"
        title_patterns = [
            f"{author_ko}이(가) 경고한 미래가 현실이 되었다 ({ko_title} 깊이 읽기)" if author_ko else f"{ko_title}이(가) 예언한 미래가 현실이 되었다",
            f"{author_ko}이(가) 말한 인생의 진실 ({ko_title} 완전 정리)" if author_ko else f"{ko_title}이(가) 전하는 인생의 진실",
            f"{author_ko}이(가) 그려낸 인간의 초상 ({ko_title} 심층 분석)" if author_ko else f"{ko_title}이(가) 그려낸 인간의 초상",
            f"{ko_title}이(가) 던진 질문, 우리는 답할 수 있을까",
            f"{author_ko}이(가) 보여준 세상의 단면 ({ko_title} 해석)" if author_ko else f"{ko_title}이(가) 보여준 세상의 단면",
        ]
        
        # 가장 적합한 패턴 선택 (간단한 휴리스틱)
        # 제목 길이와 키워드 포함 여부를 고려
        best_title = title_patterns[0]  # 기본값
        
        for pattern in title_patterns:
            if len(pattern) <= 80 and ko_title in pattern:
                best_title = pattern
                break
        
        return best_title
        
    else:  # en
        if not is_english_title(book_title):
            en_title = translate_book_title(book_title)
        else:
            en_title = book_title
        
        # 작가 이름 번역
        author_en = ""
        if author:
            if not is_english_title(author):
                author_en = translate_author_name(author)
            else:
                author_en = author
        
        # 인문학적 가치를 강조하는 제목 패턴 생성
        title_patterns = [
            f"The Future {author_en} Warned Us About ({en_title} Deep Dive)" if author_en else f"The Future {en_title} Predicted",
            f"The Truth {author_en} Revealed ({en_title} Complete Analysis)" if author_en else f"The Truth {en_title} Reveals",
            f"The Human Portrait {author_en} Drew ({en_title} In-Depth Review)" if author_en else f"The Human Portrait {en_title} Draws",
            f"The Question {en_title} Asks: Can We Answer?",
            f"The World {author_en} Showed Us ({en_title} Interpretation)" if author_en else f"The World {en_title} Shows Us",
        ]
        
        # 가장 적합한 패턴 선택
        best_title = title_patterns[0]  # 기본값
        
        for pattern in title_patterns:
            if len(pattern) <= 80 and en_title in pattern:
                best_title = pattern
                break
        
        return best_title


def generate_value_focused_title(
    book_title: str,
    author: Optional[str] = None,
    language: str = "ko",
    book_info: Optional[Dict] = None,
    use_ai_title: bool = False  # AI 생성 제목 사용 여부 (기본값: False)
) -> str:
    """
    가치 중심 제목 생성 (AI 강조 제거)
    
    use_ai_title이 False이면 인문학적 가치를 강조하는 제목을 생성합니다.
    use_ai_title이 True이면 기존 형식을 유지합니다 (하위 호환성).
    
    Args:
        book_title: 책 제목
        author: 저자 이름
        language: 언어 ('ko' 또는 'en')
        book_info: 책 정보 딕셔너리 (선택사항)
        use_ai_title: AI 강조 제목 사용 여부 (기본값: False)
        
    Returns:
        생성된 제목
    """
    if use_ai_title:
        # 기존 형식 유지 (하위 호환성)
        from src.utils.translations import (
            translate_book_title,
            translate_book_title_to_korean,
            translate_author_name,
            is_english_title
        )
        
        if language == "ko":
            if is_english_title(book_title):
                ko_title = translate_book_title_to_korean(book_title)
            else:
                ko_title = book_title
            
            author_part = ""
            if author:
                if is_english_title(author):
                    author_ko = translate_author_name(author)
                    author_part = f" {author_ko}"
                else:
                    author_part = f" {author}"
            
            return f"[핵심 요약] {ko_title} 핵심 정리{author_part}"
        else:
            if not is_english_title(book_title):
                en_title = translate_book_title(book_title)
            else:
                en_title = book_title
            
            author_part = ""
            if author:
                if not is_english_title(author):
                    author_en = translate_author_name(author)
                    author_part = f" {author_en}"
                else:
                    author_part = f" {author}"
            
            return f"[Summary] {en_title} Book Review{author_part}"
    else:
        # 인문학적 가치 강조 제목 생성
        return generate_engaging_title(book_title, author, language, book_info)


def generate_hook_title(
    book_title: str,
    author: Optional[str] = None,
    language: str = "ko",
    book_info: Optional[Dict] = None,
) -> str:
    """
    훅 카피 + 파이프 포맷의 제목 생성 (CTR 최적화)

    포맷: "{저자}이 밝힌 {인사이트} | {책제목} 핵심 요약"
    예: "프란스 드 발이 밝힌 권력의 본질 | 침팬지 폴리틱스 핵심 요약"
    예: "Frans de Waal on the Nature of Power | Chimpanzee Politics Summary"

    YouTube 100자 제한 준수, 검색어(책 제목)는 반드시 포함.
    """

    def _truncate(text: str, max_len: int = 100) -> str:
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def _guess_genre() -> str:
        if not book_info:
            return "general"
        cats = book_info.get("categories") or []
        if isinstance(cats, str):
            cats = [cats]
        desc = book_info.get("description") or ""
        text = (" ".join(cats) + " " + desc).lower()
        if any(k in text for k in ["philosophy", "철학"]):
            return "philosophy"
        if any(k in text for k in ["psychology", "self-help", "자기계발", "심리"]):
            return "psychology"
        if any(k in text for k in ["business", "economics", "경제", "경영"]):
            return "business"
        if any(k in text for k in ["history", "역사"]):
            return "history"
        if any(k in text for k in ["science", "과학"]):
            return "science"
        if any(k in text for k in ["fiction", "novel", "소설"]):
            return "fiction"
        return "general"

    genre = _guess_genre()

    # 장르별 훅 동사/구절 템플릿 (저자 있는 경우)
    # 한글 포맷: "{저자}이 밝힌 {인사이트} | {책제목} 핵심 요약"
    hook_ko_with_author = {
        "philosophy": ("{author}이 말한 삶의 본질", "{title} 핵심 요약"),
        "psychology": ("{author}이 밝힌 인간 심리의 비밀", "{title} 핵심 요약"),
        "business":   ("{author}이 제시한 성공의 법칙", "{title} 핵심 요약"),
        "history":    ("{author}이 기록한 역사의 교훈", "{title} 핵심 요약"),
        "science":    ("{author}이 설명한 세계의 원리", "{title} 핵심 요약"),
        "fiction":    ("{author}이 그린 인간의 초상", "{title} 핵심 요약"),
        "general":    ("{author}이 전하는 핵심 메시지", "{title} 핵심 요약"),
    }
    # 한글 포맷: "{책제목}이 던진 질문" (저자 없는 경우)
    hook_ko_no_author = {
        "philosophy": ("{title}이 던진 삶의 질문", "{title} 핵심 요약"),
        "psychology": ("{title}로 보는 인간 심리", "{title} 핵심 요약"),
        "business":   ("{title}의 핵심 전략", "{title} 핵심 요약"),
        "history":    ("{title}에서 배우는 역사", "{title} 핵심 요약"),
        "science":    ("{title}이 밝힌 세계의 원리", "{title} 핵심 요약"),
        "fiction":    ("{title}이 그린 세계", "{title} 핵심 요약"),
        "general":    ("{title}의 핵심 메시지", "{title} 핵심 요약"),
    }
    # 영문 포맷: "{author} on {insight} | {title} Summary"
    hook_en_with_author = {
        "philosophy": ("{author} on the Essence of Life", "{title} Summary"),
        "psychology": ("{author} on the Secrets of Human Mind", "{title} Summary"),
        "business":   ("{author} on the Rules of Success", "{title} Summary"),
        "history":    ("{author} on Lessons from History", "{title} Summary"),
        "science":    ("{author} on How the World Works", "{title} Summary"),
        "fiction":    ("{author} on the Human Condition", "{title} Summary"),
        "general":    ("{author} on the Core Message", "{title} Summary"),
    }
    hook_en_no_author = {
        "philosophy": ("The Life Question {title} Asks", "{title} Summary"),
        "psychology": ("{title} and Human Psychology", "{title} Summary"),
        "business":   ("Core Strategies from {title}", "{title} Summary"),
        "history":    ("History Lessons from {title}", "{title} Summary"),
        "science":    ("How the World Works: {title}", "{title} Summary"),
        "fiction":    ("The World of {title}", "{title} Summary"),
        "general":    ("Key Insights from {title}", "{title} Summary"),
    }

    if language == "ko":
        if author:
            hook_template, suffix_template = hook_ko_with_author.get(genre, hook_ko_with_author["general"])
            hook = hook_template.format(author=author)
        else:
            hook_template, suffix_template = hook_ko_no_author.get(genre, hook_ko_no_author["general"])
            hook = hook_template.format(title=book_title)
        suffix = suffix_template.format(title=book_title)
        title = f"{hook} | {suffix}"
    else:
        if author:
            hook_template, suffix_template = hook_en_with_author.get(genre, hook_en_with_author["general"])
            hook = hook_template.format(author=author)
        else:
            hook_template, suffix_template = hook_en_no_author.get(genre, hook_en_no_author["general"])
            hook = hook_template.format(title=book_title)
        suffix = suffix_template.format(title=book_title)
        title = f"{hook} | {suffix}"

    return _truncate(title, 100)
