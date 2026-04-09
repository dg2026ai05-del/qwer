import streamlit as st
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
import pandas as pd
import isodate
from datetime import datetime

# ──────────────────────────────────────────
# 페이지 기본 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="YouTube 댓글 수집기",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 YouTube 댓글 수집기")
st.markdown("YouTube 영상 링크를 입력하면 댓글을 가져옵니다!")

# ──────────────────────────────────────────
# API 키 불러오기 (Streamlit Secrets)
# ──────────────────────────────────────────
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("⚠️ YouTube API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에 YOUTUBE_API_KEY를 등록해주세요.")
    st.stop()

# ──────────────────────────────────────────
# 유틸 함수
# ──────────────────────────────────────────
def extract_video_id(url: str) -> str | None:
    """다양한 YouTube URL 형식에서 video ID 추출"""
    url = url.strip()
    
    # youtu.be 단축 URL
    if "youtu.be" in url:
        path = urlparse(url).path
        return path.lstrip("/").split("?")[0]
    
    # 일반 youtube.com URL
    parsed = urlparse(url)
    if "youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        # /shorts/ 형식
        if "/shorts/" in parsed.path:
            return parsed.path.split("/shorts/")[1].split("/")[0]
        # /embed/ 형식
        if "/embed/" in parsed.path:
            return parsed.path.split("/embed/")[1].split("/")[0]
    
    # video ID 직접 입력 (11자리)
    if len(url) == 11 and url.isalnum() or (len(url) == 11):
        return url
    
    return None


def get_video_info(youtube, video_id: str) -> dict:
    """영상 기본 정보 가져오기"""
    response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    ).execute()
    
    if not response["items"]:
        return {}
    
    item = response["items"][0]
    snippet = item["snippet"]
    stats = item.get("statistics", {})
    details = item.get("contentDetails", {})
    
    # 영상 길이 변환
    duration_str = details.get("duration", "PT0S")
    try:
        duration = isodate.parse_duration(duration_str)
        total_seconds = int(duration.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            duration_display = f"{hours}시간 {minutes}분 {seconds}초"
        else:
            duration_display = f"{minutes}분 {seconds}초"
    except Exception:
        duration_display = "알 수 없음"

    return {
        "제목": snippet.get("title", ""),
        "채널명": snippet.get("channelTitle", ""),
        "게시일": snippet.get("publishedAt", "")[:10],
        "조회수": int(stats.get("viewCount", 0)),
        "좋아요": int(stats.get("likeCount", 0)),
        "댓글수": int(stats.get("commentCount", 0)),
        "영상 길이": duration_display,
        "썸네일": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
    }


def get_comments(youtube, video_id: str, max_results: int = 100, order: str = "relevance") -> list[dict]:
    """댓글 가져오기 (페이지 토큰 활용)"""
    comments = []
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
            if "commentsDisabled" in error_msg or "disabled comments" in error_msg.lower():
                st.warning("⚠️ 이 영상은 댓글이 비활성화되어 있습니다.")
            else:
                st.error(f"댓글을 가져오는 중 오류 발생: {error_msg}")
            break
        
        for item in response.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "작성자": top.get("authorDisplayName", ""),
                "댓글 내용": top.get("textDisplay", ""),
                "좋아요 수": top.get("likeCount", 0),
                "답글 수": item["snippet"].get("totalReplyCount", 0),
                "작성일": top.get("publishedAt", "")[:10],
            })
        
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    
    return comments

# ──────────────────────────────────────────
# 사이드바 설정
# ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")
    
    max_comments = st.slider(
        "가져올 댓글 수",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        help="최대 500개까지 가져올 수 있습니다."
    )
    
    order = st.radio(
        "댓글 정렬 기준",
        options=["relevance", "time"],
        format_func=lambda x: "🔥 관련성순" if x == "relevance" else "🕐 최신순",
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 📌 사용 방법")
    st.markdown("""
    1. YouTube 영상 링크 입력
    2. 설정에서 댓글 수 / 정렬 선택
    3. **댓글 불러오기** 버튼 클릭
    4. 결과 확인 및 CSV 다운로드
    """)
    
    st.markdown("---")
    st.markdown("### 🔗 지원 URL 형식")
    st.code("""
youtube.com/watch?v=VIDEO_ID
youtu.be/VIDEO_ID
youtube.com/shorts/VIDEO_ID
youtube.com/embed/VIDEO_ID
    """)

# ──────────────────────────────────────────
# 메인 입력 영역
# ──────────────────────────────────────────
url_input = st.text_input(
    "🔗 YouTube 영상 링크를 입력하세요",
    placeholder="예: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    help="다양한 YouTube URL 형식을 지원합니다."
)

col1, col2 = st.columns([1, 5])
with col1:
    fetch_button = st.button("🚀 댓글 불러오기", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ 초기화", use_container_width=False)

if clear_button:
    st.rerun()

# ──────────────────────────────────────────
# 댓글 불러오기 실행
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
    
    # ── 영상 정보 출력 ──
    with st.spinner("📹 영상 정보를 불러오는 중..."):
        info = get_video_info(youtube, video_id)
    
    if not info:
        st.error("❌ 영상 정보를 찾을 수 없습니다. Video ID를 확인해주세요.")
        st.stop()
    
    st.markdown("---")
    st.subheader("📹 영상 정보")
    
    info_col1, info_col2 = st.columns([1, 2])
    with info_col1:
        if info["썸네일"]:
            st.image(info["썸네일"], use_container_width=True)
    with info_col2:
        st.markdown(f"**🎬 제목:** {info['제목']}")
        st.markdown(f"**📺 채널:** {info['채널명']}")
        st.markdown(f"**📅 게시일:** {info['게시일']}")
        st.markdown(f"**⏱️ 영상 길이:** {info['영상 길이']}")
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("👁️ 조회수", f"{info['조회수']:,}")
        metric_col2.metric("👍 좋아요", f"{info['좋아요']:,}")
        metric_col3.metric("💬 총 댓글", f"{info['댓글수']:,}")
    
    # ── 댓글 불러오기 ──
    st.markdown("---")
    st.subheader(f"💬 댓글 목록 (최대 {max_comments}개)")
    
    with st.spinner(f"💬 댓글을 불러오는 중... (최대 {max_comments}개)"):
        comments = get_comments(youtube, video_id, max_results=max_comments, order=order)
    
    if not comments:
        st.info("불러온 댓글이 없습니다.")
        st.stop()
    
    df = pd.DataFrame(comments)
    
    # ── 통계 요약 ──
    st.markdown(f"✅ **총 {len(df)}개의 댓글을 불러왔습니다.**")
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    stat_col1.metric("💬 수집된 댓글", f"{len(df)}개")
    stat_col2.metric("👍 평균 좋아요", f"{df['좋아요 수'].mean():.1f}")
    stat_col3.metric("💬 총 답글 수", f"{df['답글 수'].sum():,}")
    
    # ── 검색 필터 ──
    st.markdown("---")
    search_keyword = st.text_input("🔍 댓글 내용 검색 (키워드 입력)", placeholder="키워드를 입력하면 필터링됩니다.")
    
    if search_keyword:
        filtered_df = df[df["댓글 내용"].str.contains(search_keyword, case=False, na=False)]
        st.info(f"🔍 '{search_keyword}' 검색 결과: {len(filtered_df)}개")
        display_df = filtered_df
    else:
        display_df = df
    
    # ── 댓글 테이블 출력 ──
    st.dataframe(
        display_df,
        use_container_width=True,
        height=450,
        column_config={
            "작성자": st.column_config.TextColumn("작성자", width="small"),
            "댓글 내용": st.column_config.TextColumn("댓글 내용", width="large"),
            "좋아요 수": st.column_config.NumberColumn("👍 좋아요", width="small"),
            "답글 수": st.column_config.NumberColumn("💬 답글", width="small"),
            "작성일": st.column_config.DateColumn("📅 작성일", width="small"),
        }
    )
    
    # ── CSV 다운로드 ──
    st.markdown("---")
    csv_data = df.to_csv(index=False, encoding="utf-8-sig")
    file_name = f"youtube_comments_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    st.download_button(
        label="⬇️ CSV로 다운로드",
        data=csv_data,
        file_name=file_name,
        mime="text/csv",
        type="primary"
    )
    
    st.caption("💡 CSV 파일은 Excel에서 열면 한글이 깨지지 않습니다. (utf-8-sig 인코딩 적용)")
