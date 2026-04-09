import streamlit as st
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
import pandas as pd
import isodate
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from wordcloud import WordCloud
from collections import Counter
import re
import os
import urllib.request

# ──────────────────────────────────────────
# 페이지 기본 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="🎬 YouTube 댓글 분석기",
    page_icon="🎬",
    layout="wide",
)

# ──────────────────────────────────────────
# 커스텀 CSS (알록달록 귀여운 스타일)
# ──────────────────────────────────────────
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background: linear-gradient(135deg, #667eea22 0%, #764ba222 50%, #f093fb22 100%);
    }

    /* 메인 타이틀 */
    .main-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(90deg, #FF6B6B, #FFE66D, #4ECDC4, #45B7D1, #96CEB4, #FF6B9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: rainbow 3s ease-in-out infinite;
        background-size: 300% 300%;
        margin-bottom: 0.2rem;
    }
    @keyframes rainbow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 서브타이틀 */
    .sub-title {
        text-align: center;
        font-size: 1.1rem;
        color: #888;
        margin-bottom: 2rem;
    }

    /* 카드 스타일 */
    .cute-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        margin: 0.8rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 2px solid transparent;
        background-clip: padding-box;
    }

    /* 섹션 헤더 */
    .section-header {
        font-size: 1.4rem;
        font-weight: 800;
        margin: 1.5rem 0 1rem 0;
        padding: 0.6rem 1.2rem;
        border-radius: 50px;
        display: inline-block;
    }

    .header-pink {
        background: linear-gradient(90deg, #FF6B9D22, #FF8E5322);
        color: #FF6B9D;
        border: 2px solid #FF6B9D44;
    }
    .header-blue {
        background: linear-gradient(90deg, #45B7D122, #667eea22);
        color: #45B7D1;
        border: 2px solid #45B7D144;
    }
    .header-green {
        background: linear-gradient(90deg, #96CEB422, #4ECDC422);
        color: #27AE60;
        border: 2px solid #96CEB444;
    }
    .header-purple {
        background: linear-gradient(90deg, #764ba222, #667eea22);
        color: #764ba2;
        border: 2px solid #764ba244;
    }
    .header-yellow {
        background: linear-gradient(90deg, #FFE66D22, #FFA07A22);
        color: #E67E22;
        border: 2px solid #FFE66D88;
    }

    /* 메트릭 카드 */
    .metric-card {
        border-radius: 18px;
        padding: 1.2rem;
        text-align: center;
        color: white;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-3px); }

    .metric-pink   { background: linear-gradient(135deg, #FF6B9D, #FF8E53); }
    .metric-blue   { background: linear-gradient(135deg, #45B7D1, #667eea); }
    .metric-green  { background: linear-gradient(135deg, #96CEB4, #4ECDC4); }
    .metric-purple { background: linear-gradient(135deg, #764ba2, #667eea); }
    .metric-yellow { background: linear-gradient(135deg, #FFE66D, #FFA07A); }

    .metric-number { font-size: 1.8rem; margin: 0.3rem 0; }
    .metric-label  { font-size: 0.85rem; opacity: 0.9; }

    /* 키워드 뱃지 */
    .keyword-badge {
        display: inline-block;
        padding: 0.35rem 0.9rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 700;
        margin: 0.25rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        transition: transform 0.15s;
        cursor: default;
    }
    .keyword-badge:hover { transform: scale(1.08); }

    /* TOP 키워드 테이블 */
    .keyword-row {
        display: flex;
        align-items: center;
        padding: 0.6rem 1rem;
        border-radius: 12px;
        margin: 0.3rem 0;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: transform 0.15s;
    }
    .keyword-row:hover { transform: translateX(5px); }

    /* 구분선 */
    .divider {
        height: 3px;
        background: linear-gradient(90deg, #FF6B6B, #FFE66D, #4ECDC4, #45B7D1, #FF6B9D);
        border-radius: 10px;
        margin: 1.5rem 0;
    }

    /* 풍선 애니메이션 이모지 */
    .bounce {
        display: inline-block;
        animation: bounce 1s infinite alternate;
    }
    @keyframes bounce {
        from { transform: translateY(0); }
        to   { transform: translateY(-6px); }
    }

    /* Streamlit 기본 요소 커스텀 */
    div[data-testid="stButton"] button {
        border-radius: 50px !important;
        font-weight: 700 !important;
    }
    div[data-testid="stTextInput"] input {
        border-radius: 50px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 0.6rem 1rem !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #FF6B9D !important;
        box-shadow: 0 0 0 3px #FF6B9D22 !important;
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fff0f6, #f0f4ff) !important;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 타이틀
# ──────────────────────────────────────────
st.markdown('<div class="main-title">🎬 YouTube 댓글 분석기 ✨</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">💬 댓글을 한 번에 수집하고 🔍 키워드까지 분석해드려요!</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────
# API 키
# ──────────────────────────────────────────
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("⚠️ YouTube API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에 YOUTUBE_API_KEY를 등록해주세요.")
    st.stop()

# ──────────────────────────────────────────
# 한국어 폰트 다운로드 & 설정
# ──────────────────────────────────────────
@st.cache_resource
def load_korean_font():
    """Noto Sans KR 폰트 다운로드 (워드클라우드용)"""
    font_path = "/tmp/NanumGothic.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            font_path = None
    return font_path

font_path = load_korean_font()

# ──────────────────────────────────────────
# 불용어 (분석에서 제외할 단어)
# ──────────────────────────────────────────
STOPWORDS = set([
    "이", "가", "을", "를", "은", "는", "의", "에", "에서", "로", "으로",
    "와", "과", "도", "만", "까지", "부터", "한테", "이랑", "랑",
    "그", "저", "이것", "저것", "그것", "여기", "거기", "저기",
    "하다", "있다", "없다", "되다", "이다", "아니다", "같다",
    "하고", "하지", "하는", "하면", "해서", "해요", "합니다", "했어요",
    "그리고", "그런데", "그래서", "하지만", "근데", "그냥", "진짜",
    "정말", "너무", "매우", "아주", "좀", "더", "또", "다",
    "ㅋㅋ", "ㅎㅎ", "ㅠㅠ", "ㅜㅜ", "ㄷㄷ", "ㅠ", "ㅜ", "ㅋ", "ㅎ",
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "do", "does", "did", "will", "would", "can",
    "could", "should", "may", "might", "shall", "and", "or",
    "but", "if", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "through", "it", "its",
    "this", "that", "i", "you", "he", "she", "we", "they",
    "my", "your", "his", "her", "our", "their", "what", "so",
])

# ──────────────────────────────────────────
# 유틸 함수
# ──────────────────────────────────────────
def extract_video_id(url: str):
    url = url.strip()
    if "youtu.be" in url:
        return urlparse(url).path.lstrip("/").split("?")[0]
    parsed = urlparse(url)
    if "youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        if "/shorts/" in parsed.path:
            return parsed.path.split("/shorts/")[1].split("/")[0]
        if "/embed/" in parsed.path:
            return parsed.path.split("/embed/")[1].split("/")[0]
    if len(url) == 11:
        return url
    return None


def get_video_info(youtube, video_id):
    response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    ).execute()
    if not response["items"]:
        return {}
    item     = response["items"][0]
    snippet  = item["snippet"]
    stats    = item.get("statistics", {})
    details  = item.get("contentDetails", {})

    duration_str = details.get("duration", "PT0S")
    try:
        duration        = isodate.parse_duration(duration_str)
        total_seconds   = int(duration.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes  = divmod(minutes, 60)
        duration_display = (
            f"{hours}시간 {minutes}분 {seconds}초" if hours > 0
            else f"{minutes}분 {seconds}초"
        )
    except Exception:
        duration_display = "알 수 없음"

    return {
        "제목":     snippet.get("title", ""),
        "채널명":   snippet.get("channelTitle", ""),
        "게시일":   snippet.get("publishedAt", "")[:10],
        "조회수":   int(stats.get("viewCount", 0)),
        "좋아요":   int(stats.get("likeCount", 0)),
        "댓글수":   int(stats.get("commentCount", 0)),
        "영상길이": duration_display,
        "썸네일":   snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
    }


def get_comments(youtube, video_id, max_results=100, order="relevance"):
    comments       = []
    next_page_token = None
    while len(comments) < max_results:
        fetch_count = min(100, max_results - len(comments))
        try:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=fetch_count,
                order=order,
                pageToken=next_page_token,
                textFormat="plainText"
            ).execute()
        except Exception as e:
            error_msg = str(e)
            if "commentsDisabled" in error_msg:
                st.warning("⚠️ 이 영상은 댓글이 비활성화되어 있습니다.")
            else:
                st.error(f"댓글을 가져오는 중 오류 발생: {error_msg}")
            break

        for item in response.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "작성자":    top.get("authorDisplayName", ""),
                "댓글 내용": top.get("textDisplay", ""),
                "좋아요 수": top.get("likeCount", 0),
                "답글 수":   item["snippet"].get("totalReplyCount", 0),
                "작성일":    top.get("publishedAt", "")[:10],
            })
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return comments


def extract_keywords(comments_list, top_n=30):
    """댓글에서 키워드 추출 (형태소 분석 없이 regex 기반)"""
    all_text = " ".join(comments_list)

    # 한국어 단어 (2글자 이상)
    korean_words = re.findall(r"[가-힣]{2,}", all_text)
    # 영어 단어 (3글자 이상)
    english_words = re.findall(r"[a-zA-Z]{3,}", all_text.lower())
    # 숫자+한글 조합 제외, 이모지 제외
    all_words = korean_words + english_words

    # 불용어 제거
    filtered = [w for w in all_words if w not in STOPWORDS and len(w) >= 2]

    counter = Counter(filtered)
    return counter.most_common(top_n)


def make_wordcloud(word_freq: dict, font_path=None):
    """워드클라우드 생성"""
    colors = ["#FF6B6B", "#FF6B9D", "#FFE66D", "#4ECDC4",
              "#45B7D1", "#96CEB4", "#667eea", "#764ba2", "#FFA07A"]

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        import random
        return random.choice(colors)

    wc_kwargs = dict(
        width=900,
        height=450,
        background_color="white",
        color_func=color_func,
        max_words=80,
        prefer_horizontal=0.7,
        margin=10,
        collocations=False,
    )
    if font_path and os.path.exists(font_path):
        wc_kwargs["font_path"] = font_path

    wc = WordCloud(**wc_kwargs)
    wc.generate_from_frequencies(word_freq)
    return wc


# 순위별 뱃지 색상
BADGE_COLORS = [
    ("#FF6B9D", "#fff0f6"),  # 1위  핑크
    ("#FF8E53", "#fff5f0"),  # 2위  오렌지
    ("#FFE66D", "#fffdf0"),  # 3위  옐로우
    ("#4ECDC4", "#f0fffe"),  # 4위  민트
    ("#45B7D1", "#f0f8ff"),  # 5위  스카이블루
    ("#667eea", "#f4f0ff"),  # 6위  인디고
    ("#764ba2", "#f8f0ff"),  # 7위  퍼플
    ("#96CEB4", "#f0fff6"),  # 8위  세이지그린
    ("#FFA07A", "#fff5f0"),  # 9위  살몬
    ("#87CEEB", "#f0f8ff"),  # 10위 라이트블루
]

RANK_EMOJI = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣",
              "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

KEYWORD_EMOJI = {
    # 감정
    "좋아": "❤️", "사랑": "💕", "행복": "😊", "슬픔": "😢", "화남": "😠",
    "웃음": "😂", "감사": "🙏", "최고": "👑", "최애": "💗", "힘내": "💪",
    # 콘텐츠
    "음악": "🎵", "노래": "🎤", "춤": "💃", "영상": "🎬", "게임": "🎮",
    "요리": "🍳", "여행": "✈️", "운동": "🏃", "공부": "📚", "책": "📖",
    # 사람
    "선생": "👨‍🏫", "친구": "👫", "가족": "👨‍👩‍👧", "아이": "👶", "학생": "🎓",
    # 자연
    "봄": "🌸", "여름": "☀️", "가을": "🍂", "겨울": "❄️",
    "꽃": "🌺", "강아지": "🐶", "고양이": "🐱",
    # 기타
    "돈": "💰", "맛있": "😋", "예쁘": "✨", "귀여": "🥰", "멋있": "😎",
}

def get_keyword_emoji(word):
    for key, emoji in KEYWORD_EMOJI.items():
        if key in word:
            return emoji
    return "💬"


# ──────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")

    max_comments = st.slider(
        "💬 가져올 댓글 수",
        min_value=10, max_value=500, value=100, step=10,
    )
    order = st.radio(
        "📊 댓글 정렬",
        options=["relevance", "time"],
        format_func=lambda x: "🔥 관련성순" if x == "relevance" else "🕐 최신순",
    )
    top_keyword_n = st.slider(
        "🔑 표시할 키워드 수",
        min_value=5, max_value=30, value=15, step=1,
    )

    st.markdown("---")
    st.markdown("### 📌 사용 방법")
    st.markdown("""
    1. 🔗 YouTube 링크 입력
    2. ⚙️ 사이드바에서 설정 조절
    3. 🚀 **분석 시작** 버튼 클릭
    4. 📊 결과 확인 & 💾 CSV 저장
    """)

    st.markdown("---")
    st.markdown("### 🔗 지원 URL")
    st.code("""
youtube.com/watch?v=ID
youtu.be/ID
youtube.com/shorts/ID
    """)

# ──────────────────────────────────────────
# 메인 입력
# ──────────────────────────────────────────
url_input = st.text_input(
    "🔗 YouTube 영상 링크를 입력하세요",
    placeholder="예: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
)

col_btn1, col_btn2, col_space = st.columns([1.2, 0.8, 4])
with col_btn1:
    fetch_button = st.button("🚀 분석 시작!", type="primary", use_container_width=True)
with col_btn2:
    clear_button = st.button("🗑️ 초기화", use_container_width=True)

if clear_button:
    st.rerun()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────
# 분석 실행
# ──────────────────────────────────────────
if fetch_button:
    if not url_input.strip():
        st.warning("⚠️ YouTube 링크를 입력해주세요!")
        st.stop()

    video_id = extract_video_id(url_input)
    if not video_id:
        st.error("❌ 올바른 YouTube URL을 입력해주세요.")
        st.stop()

    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
    except Exception as e:
        st.error(f"API 연결 실패: {e}")
        st.stop()

    # ── 영상 정보 ──────────────────────────
    st.markdown('<div class="section-header header-pink">📹 영상 정보</div>', unsafe_allow_html=True)

    with st.spinner("📹 영상 정보를 불러오는 중..."):
        info = get_video_info(youtube, video_id)

    if not info:
        st.error("❌ 영상 정보를 찾을 수 없습니다.")
        st.stop()

    info_col1, info_col2 = st.columns([1, 2.5])
    with info_col1:
        if info["썸네일"]:
            st.image(info["썸네일"], use_container_width=True)
    with info_col2:
        st.markdown(f"### 🎬 {info['제목']}")
        st.markdown(f"📺 **채널:** {info['채널명']}  |  📅 **게시일:** {info['게시일']}  |  ⏱️ **길이:** {info['영상길이']}")

        m1, m2, m3 = st.columns(3)
        m1.markdown(f"""
        <div class="metric-card metric-pink">
            <div class="metric-label">👁️ 조회수</div>
            <div class="metric-number">{info['조회수']:,}</div>
        </div>""", unsafe_allow_html=True)
        m2.markdown(f"""
        <div class="metric-card metric-blue">
            <div class="metric-label">👍 좋아요</div>
            <div class="metric-number">{info['좋아요']:,}</div>
        </div>""", unsafe_allow_html=True)
        m3.markdown(f"""
        <div class="metric-card metric-green">
            <div class="metric-label">💬 총 댓글</div>
            <div class="metric-number">{info['댓글수']:,}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── 댓글 수집 ──────────────────────────
    st.markdown('<div class="section-header header-blue">💬 댓글 수집 중...</div>', unsafe_allow_html=True)

    progress_bar = st.progress(0, text="🔄 댓글 수집 시작!")
    with st.spinner(f"💬 댓글 {max_comments}개를 불러오는 중..."):
        progress_bar.progress(20, text="📡 YouTube API 연결 중...")
        comments = get_comments(youtube, video_id, max_results=max_comments, order=order)
        progress_bar.progress(60, text="📝 댓글 데이터 처리 중...")

    if not comments:
        st.info("불러온 댓글이 없습니다.")
        st.stop()

    df = pd.DataFrame(comments)
    progress_bar.progress(80, text="🔍 키워드 분석 중...")

    # ── 키워드 분석 ────────────────────────
    all_comments_text = df["댓글 내용"].tolist()
    top_keywords = extract_keywords(all_comments_text, top_n=top_keyword_n)
    progress_bar.progress(100, text="✅ 분석 완료!")
    st.balloons()

    # ── 수집 요약 통계 ──────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header header-yellow">📊 수집 요약</div>', unsafe_allow_html=True)

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.markdown(f"""<div class="metric-card metric-pink">
        <div class="metric-label">💬 수집 댓글</div>
        <div class="metric-number">{len(df)}</div>
        <div class="metric-label">개</div>
    </div>""", unsafe_allow_html=True)
    s2.markdown(f"""<div class="metric-card metric-blue">
        <div class="metric-label">👍 평균 좋아요</div>
        <div class="metric-number">{df['좋아요 수'].mean():.1f}</div>
    </div>""", unsafe_allow_html=True)
    s3.markdown(f"""<div class="metric-card metric-green">
        <div class="metric-label">💬 총 답글</div>
        <div class="metric-number">{df['답글 수'].sum():,}</div>
        <div class="metric-label">개</div>
    </div>""", unsafe_allow_html=True)
    s4.markdown(f"""<div class="metric-card metric-purple">
        <div class="metric-label">🔑 발견 키워드</div>
        <div class="metric-number">{len(top_keywords)}</div>
        <div class="metric-label">개</div>
    </div>""", unsafe_allow_html=True)
    s5.markdown(f"""<div class="metric-card metric-yellow">
        <div class="metric-label">👑 최다 좋아요</div>
        <div class="metric-number">{df['좋아요 수'].max():,}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ────────────────────────────────────────
    # 🔑 키워드 분석 섹션
    # ────────────────────────────────────────
    st.markdown('<div class="section-header header-purple">🔑 키워드 분석 결과</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🏆 TOP 키워드 순위", "☁️ 워드클라우드", "📊 막대 차트"])

    # ── TAB 1 : TOP 키워드 순위 ─────────────
    with tab1:
        if not top
