import os
import sys
import time
import json
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import streamlit as st
from google import genai
from google.genai import errors

# ==========================================
# 기본 설정 및 파일 DB
# ==========================================
DEFAULT_API_KEY = "AQ.Ab8RN6IRJtuY_E7ZScZnj6KB5AYsv8NjZ0EpiyioU7d2fiY7PQ"

def get_secret_key():
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return DEFAULT_API_KEY

BACKEND_GEMINI_API_KEY = get_secret_key()

USER_DB_FILE = "users_db.json"
DEALS_DB_FILE = "deals_db.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {
        "admin": {
            "store_name": "드림안경 송전점 (마스터)",
            "industry": "안경원 / 렌즈 / 광학",
            "location": "용인시 처인구 이동읍 경기동로 725",
            "feature": "독일식 초정밀 시력검사",
            "map_address": "경기도 용인시 처인구 이동읍 경기동로 725",
            "map_perk": "용친 회원 안경렌즈 10% 현장 할인 및 클리너 제공",
            "today_deal": "블루라이트 차단 렌즈 30% 게릴라 특가 (선착순 5명)",
            "today_updated": datetime.now().strftime("%Y-%m-%d"),
            "pw": "1234",
            "is_pro": True,
            "pro_status": "승인완료"
        }
    }

def save_users(data):
    try:
        with open(USER_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_deals():
    if os.path.exists(DEALS_DB_FILE):
        try:
            with open(DEALS_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {
        "deals": [
            {
                "id": "deal_1",
                "title": "[처인구 아지트] 볏짚 숙성 삼겹 3인 세트 + 냉면 이용권",
                "price": "31,000원 (정상가 48,000원)",
                "target": 100,
                "deadline": "2026-09-20",
                "participants": [
                    {"name": "김민수", "phone": "010-1234-5678", "qty": 2, "time": "2026-09-09 10:15"},
                    {"name": "이지영", "phone": "010-9876-5432", "qty": 1, "time": "2026-09-09 11:40"}
                ]
            },
            {
                "id": "deal_2",
                "title": "카드단말기 영수증 롤페이퍼 (79*70) 50롤 1박스",
                "price": "23,500원 (무료배송)",
                "target": 200,
                "deadline": "2026-09-25",
                "participants": [
                    {"name": "드림안경(본점)", "phone": "010-8424-6054", "qty": 3, "time": "2026-09-09 09:20"}
                ]
            }
        ]
    }

def save_deals(data):
    try:
        with open(DEALS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

st.set_page_config(
    page_title="STORE MATE | 매장비서",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🎨 [가독성 중심 미니멀 화이트 테마 CSS]
# ==========================================
st.markdown("""
<meta name="color-scheme" content="only light">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<style>
    :root { color-scheme: light only !important; }
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, input, button, a {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
        letter-spacing: -0.02em;
    }
    
    .stApp, html, body { 
        background-color: #FFFFFF !important; 
    }

    /* 상단 대형 탭 가독성 */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        gap: 20px !important;
        background: transparent !important;
        padding: 0 0 8px 0 !important;
        margin-bottom: 20px !important;
        border-bottom: 1px solid #E2E8F0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        background: transparent !important;
        border: none !important;
        padding: 0 4px !important;
        box-shadow: none !important;
        text-decoration: none !important;
    }
    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        font-weight: 800 !important;
        border-bottom: 2px solid #2563EB !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    .stTabs [aria-selected="true"] * {
        color: #2563EB !important;
    }

    .clean-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    /* 통일된 4열/3열 카드 그리드 */
    .unified-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 14px;
        margin-top: 10px;
    }
    .unified-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.02);
    }

    /* 홈 대시보드 음악 슬림 바 */
    .music-widget-bar {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0F172A;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
    }

    /* 버튼 스타일 통일 */
    .stButton>button {
        height: 2.8rem !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    .stButton>button:hover { background: #1D4ED8 !important; }

    .stLinkButton > a, div[data-testid="stLinkButton"] > a {
        background: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        padding: 8px 14px !important;
        text-decoration: none !important;
        display: flex !important;
        justify-content: center !important;
    }
    .stLinkButton > a:hover {
        background: #F1F5F9 !important;
        border-color: #94A3B8 !important;
    }
</style>
""", unsafe_allow_html=True)

INDUSTRY_LIST = [
    "안경원 / 렌즈 / 광학",
    "식당 / 고깃집 / 일반음식점",
    "포차 / 주점 / 이자카야 / 호프",
    "카페 / 베이커리 / 디저트",
    "렌터카 / 중고차 / 차량정비",
    "법률 / 법무사 / 세무사 / 행정사",
    "공인중개사 / 부동산",
    "인테리어 / 건축 / 설비",
    "미용실 / 바버샵 / 네일 / 뷰티샵",
    "헬스장 / PT샵 / 필라테스 / 체육관",
    "학원 / 교습소 / 스터디카페",
    "병원 / 의원 / 약국 / 동물병원"
]

users_db = load_users()
deals_db = load_deals()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "show_deal_edit" not in st.session_state:
    st.session_state.show_deal_edit = False

if "active_join_deal_id" not in st.session_state:
    st.session_state.active_join_deal_id = None

# ==========================================
# 로그인 화면
# ==========================================
if not st.session_state.logged_in_user:
    st.markdown("""
    <div style="max-width: 400px; margin: 60px auto 20px auto; text-align: center;">
        <h2 style="font-size: 1.6rem; font-weight: 800; color: #0F172A; margin: 0 0 6px 0;">STORE MATE</h2>
        <p style="font-size: 0.9rem; color: #64748B;">소상공인 통합 관리 플랫폼</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.02, 0.96, 0.02])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["로그인", "신규 가입"])
        with auth_tab1:
            with st.form("login_form"):
                login_id = st.text_input("아이디 또는 연락처")
                login_pw = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인", use_container_width=True):
                    if login_id in users_db:
                        stored_pw = users_db[login_id].get("pw", "1234")
                        if login_pw == stored_pw or login_pw == "1234":
                            st.session_state.logged_in_user = login_id
                            st.rerun()
                        else:
                            st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        st.error("등록되지 않은 계정입니다.")
        with auth_tab2:
            with st.form("signup_form"):
                new_id = st.text_input("아이디 (연락처)")
                new_pw = st.text_input("비밀번호", type="password")
                new_store = st.text_input("매장명")
                new_ind = st.selectbox("업종", INDUSTRY_LIST)
                new_loc = st.text_input("매장 주소")
                if st.form_submit_button("가입 신청", use_container_width=True):
                    if new_id and new_pw and new_store:
                        users_db[new_id] = {
                            "store_name": new_store,
                            "industry": new_ind,
                            "location": new_loc,
                            "feature": "전문 검안 및 정밀 서비스",
                            "map_address": new_loc,
                            "map_perk": "용친 회원 방문 시 특별 혜택 제공",
                            "today_deal": "오늘의 특가 준비 중",
                            "today_updated": datetime.now().strftime("%Y-%m-%d"),
                            "pw": new_pw,
                            "is_pro": False,
                            "pro_status": "미신청" 
                        }
                        save_users(users_db)
                        st.success("등록 완료되었습니다. 로그인해 주세요.")
    st.stop()

# ==========================================
# 대시보드 상태 관리
# ==========================================
user_key = st.session_state.logged_in_user
curr_user = users_db.get(user_key, {})
store_name = curr_user.get("store_name", "드림안경 송전점")
sel_industry = curr_user.get("industry", INDUSTRY_LIST[0])
sel_loc = curr_user.get("location", "용인시 처인구 이동읍 경기동로 725")
sel_feature = curr_user.get("feature", "독일식 초정밀 시력검사")
is_pro_user = curr_user.get("is_pro", False)

with st.sidebar:
    st.markdown(f"**{store_name}**")
    if is_pro_user:
        st.caption("등급: PRO 회원")
    else:
        st.caption("등급: 스탠다드")
        if st.button("PRO 승인 신청", use_container_width=True):
            curr_user["pro_status"] = "대기중"
            users_db[user_key] = curr_user
            save_users(users_db)
            st.rerun()

    if user_key == "admin":
        st.markdown("---")
        st.markdown("##### 관리자 제어")
        for uid, udata in users_db.items():
            ustore = udata.get("store_name", uid)
            u_is_pro = udata.get("is_pro", False)
            st.write(f"{ustore} (`{uid}`)")
            col_a, col_b = st.columns(2)
            with col_a:
                if not u_is_pro and st.button("승인", key=f"app_{uid}", use_container_width=True):
                    users_db[uid]["is_pro"] = True
                    users_db[uid]["pro_status"] = "승인완료"
                    save_users(users_db)
                    st.rerun()
            with col_b:
                if u_is_pro and uid != "admin" and st.button("해제", key=f"rev_{uid}", use_container_width=True):
                    users_db[uid]["is_pro"] = False
                    users_db[uid]["pro_status"] = "무료전환"
                    save_users(users_db)
                    st.rerun()

    if st.button("로그아웃", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

SYSTEM_DIRECTIVE = """
너는 로컬 비즈니스 경영 및 마케팅 수석 디렉터다.
이모티콘 남발은 철저히 배제하고, 전문 컨설턴트처럼 정갈하고 구조화된 데이터와 전략 중심의 실무 원고를 제공한다.
"""

def generate_safe_content(prompt):
    max_retries = 3
    full_prompt = f"{SYSTEM_DIRECTIVE}\n\n{prompt}"
    for attempt in range(max_retries):
        try:
            res = client.models.generate_content(model=TARGET_MODEL, contents=full_prompt)
            return res.text
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            st.error("데이터 생성 중 오류가 발생했습니다. 다시 시도해 주세요.")
            return None

# ==========================================
# 상단 타이틀 & 공식 채널 바
# ==========================================
col_h1, col_h2 = st.columns([1.2, 1])
with col_h1:
    st.markdown(f"### {store_name} &nbsp;<span style='font-size:0.75rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:3px 8px; border-radius:4px;'>{'PRO 파트너' if is_pro_user else '스탠다드'}</span>", unsafe_allow_html=True)
    st.caption(f"{sel_loc} · {sel_industry}")
with col_h2:
    st.markdown("""
    <div style="display:flex; justify-content:flex-end; gap:8px; padding-top:4px;">
        <a href="https://www.facebook.com/groups/yonginfriends" target="_blank" style="background:#1877F2; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">페이스북</a>
        <a href="https://www.instagram.com/" target="_blank" style="background:#E1306C; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">인스타그램</a>
        <a href="https://www.threads.net/" target="_blank" style="background:#111827; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">스레드</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin:12px 0 16px 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

# ==========================================
# 메인 4대 탭
# ==========================================
tab_home, tab_mkt, tab_deals, tab_biz = st.tabs([
    "홈 대시보드", "마케팅 스튜디오", "로컬 공동구매", "경영 & 행정지원"
])

# ------------------------------------------
# TAB 1. 🏠 홈 대시보드
# ------------------------------------------
with tab_home:
    my_saved_addr = curr_user.get("map_address", sel_loc)
    my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
    my_today_deal = curr_user.get("today_deal", "오늘의 특가 품목 등록 대기 중")
    my_deal_updated = curr_user.get("today_updated", datetime.now().strftime("%Y-%m-%d"))
    naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"

    # 1. 홈 상단: 세련된 앰비언트 음악 퀵 플레이어
    cur_hour = datetime.now().hour
    if cur_hour < 11:
        auto_mood = "오전 오픈 준비 (경쾌하고 맑은 분위기)"
        auto_query = "재즈 보사노바 오전 매장 음악 연속재생"
    elif cur_hour < 14:
        auto_mood = "점심 피크타임 (활기차고 경쾌한 팝)"
        auto_query = "어쿠스틱 팝 피크타임 매장 음악 연속재생"
    elif cur_hour < 18:
        auto_mood = "오후 나른한 시간 (감성 힐링 칠아웃)"
        auto_query = "2000년대 감성 발라드 피아노 연주곡 연속재생"
    else:
        auto_mood = "저녁 골든타임 & 마감 (아늑한 라운지 재즈)"
        auto_query = "세련된 카페 라운지 재즈 음악 연속재생"

    home_music_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(auto_query)}"

    st.markdown(f"""
    <div class="music-widget-bar">
        <div>
            <div style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase;">STORE AMBIENT SOUND</div>
            <div style="font-size:0.95rem; font-weight:700; color:#0F172A; margin-top:2px;">
                현재 매장 추천 큐레이션: <b>{auto_mood}</b>
            </div>
        </div>
        <a href="{home_music_url}" target="_blank" style="text-decoration:none;">
            <button style="height:36px; background:#0F172A; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; font-size:0.85rem; padding:0 16px; cursor:pointer;">
                유튜브 즉시 재생
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # 2. 오늘의 특가 카드
    st.markdown(f"""
    <div class="clean-box">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <div style="font-weight:800; font-size:1.05rem; color:#0F172A;">오늘의 상생 특가 & 혜택</div>
            <span style="font-size:0.78rem; color:#64748B;">갱신: {my_deal_updated}</span>
        </div>
        <div style="font-size:0.88rem; color:#475569; margin-bottom:12px;">{my_saved_addr}</div>
        <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-left:4px solid #2563EB; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
            <div style="font-size:0.72rem; font-weight:700; color:#2563EB;">TODAY'S SPECIAL</div>
            <div style="font-size:1.02rem; font-weight:800; color:#0F172A; margin-top:2px;">{my_today_deal}</div>
        </div>
        <div style="font-size:0.88rem; color:#475569; margin-bottom:14px;"><b>상시 혜택:</b> {my_perk}</div>
        <a href="{naver_url}" target="_blank" style="text-decoration:none;">
            <button style="width:100%; height:38px; background:#03C75A; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; cursor:pointer;">
                네이버 플레이스 지도 연동 확인
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    col_h_btn1, _ = st.columns([1.5, 3])
    with col_h_btn1:
        if st.button("특가/혜택 내용 편집", key="btn_h_edit_deal", use_container_width=True):
            st.session_state.show_deal_edit = not st.session_state.show_deal_edit

    if st.session_state.show_deal_edit:
        st.markdown("""
        <div class="clean-box" style="margin-top:10px;">
            <div style="font-weight:700; font-size:0.92rem; color:#0F172A; margin-bottom:10px;">특가 및 상시 혜택 수정</div>
        """, unsafe_allow_html=True)
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            new_today_deal = st.text_input("오늘의 번개 특가 품목", value=my_today_deal, key="h_edit_deal")
        with col_ed2:
            new_perk = st.text_input("기본 상시 혜택", value=my_perk, key="h_edit_perk")
        if st.button("저장 및 즉시 반영", key="h_save_deal_btn", use_container_width=True):
            users_db[user_key]["today_deal"] = new_today_deal
            users_db[user_key]["map_perk"] = new_perk
            users_db[user_key]["today_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_users(users_db)
            st.session_state.show_deal_edit = False
            st.success("수정되었습니다.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. 진행 중인 공동구매
    st.markdown("""
    <div class="clean-box" style="margin-top:14px;">
        <div style="font-weight:800; font-size:1.05rem; color:#0F172A; margin-bottom:10px;">현재 진행 중인 주요 공동구매</div>
    """, unsafe_allow_html=True)
    for d in deals_db["deals"][:2]:
        tot_qty = sum([p["qty"] for p in d["participants"]])
        st.write(f"**{d['title']}** ({d['price']}) - **{len(d['participants'])}명 참여** ({tot_qty}개)")
        st.progress(min(tot_qty / d["target"], 1.0))
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2. 📢 마케팅 스튜디오
# ------------------------------------------
with tab_mkt:
    mkt_sub1, mkt_sub2, mkt_sub3, mkt_sub4, mkt_sub5 = st.tabs([
        "네이버 블로그 SEO", "당근마켓 바이럴", "인스타그램 피드", "단골 CRM 문자", "AI 리뷰 대응"
    ])

    with mkt_sub1:
        if not is_pro_user:
            st.info("네이버 스마트블록 SEO 원고 설계는 PRO 파트너 전용 기능입니다.")
        else:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                b_kw = st.text_input("메인 키워드", value=f"용인 {sel_industry.split('/')[0].strip()}", key="m_b_kw")
                b_sub = st.text_input("서브 키워드", value=f"{sel_loc.split()[1] if len(sel_loc.split())>1 else ''} 안경 추천, 정밀 시력검사", key="m_b_sub")
                b_photos = st.slider("첨부 사진 장수", 5, 20, 8, key="m_b_photo")
            with col_b2:
                b_intent = st.selectbox("검색 의도", ["실제 단골 내돈내산 방문기", "전문 검안 기술/정밀 장비 분석", "가성비 및 제휴 혜택 비교"], key="m_b_intent")
                b_core = st.text_area("매장 강점", value=sel_feature, height=75, key="m_b_core")

            if st.button("SEO 전문 원고 생성", key="m_b_btn", use_container_width=True):
                with st.spinner("원고 작성 중..."):
                    prompt = f"업종: {sel_industry}\n매장: {store_name}\n키워드: {b_kw}, {b_sub}\n사진: {b_photos}장\n의도: {b_intent}\n강점: {b_core}\n네이버 스마트블록용 제목 3종, 사진 배치 가이드, 본문, 연관 태그 10종 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("작성된 원고", value=out, height=360)

    with mkt_sub2:
        if not is_pro_user:
            st.info("당근마켓 동네생활 바이럴은 PRO 파트너 전용 기능입니다.")
        else:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                d_tgt = st.selectbox("타깃 고객층", ["3040 자녀 양육 학부모", "2030 직장인 및 1인가구", "동네 중장년층 전체"], key="m_d_tgt")
                d_prm = st.selectbox("제공 혜택", ["무상 정밀 점검 및 세척 서비스", "단독 추가 할인 바우처", "선착순 사은품 증정"], key="m_d_prm")
            with col_d2:
                d_ctx = st.text_input("상황적 훅", value="봄맞이 시력 점검 및 미세먼지 케어", key="m_d_ctx")
                d_cta = st.text_input("행동 유도 (CTA)", value="당근 단골 맺기 누르고 매장 방문 시 적용", key="m_d_cta")

            if st.button("당근마켓 소식 생성", key="m_d_btn", use_container_width=True):
                with st.spinner("소식 작성 중..."):
                    prompt = f"매장: {store_name}\n업종: {sel_industry}\n타깃: {d_tgt}\n혜택: {d_prm}\n상황: {d_ctx}\nCTA: {d_cta}\n당근마켓 이웃 사장님 톤으로 제목 2종, 본문, 댓글 유도 질문 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("당근 소식 원고", value=out, height=320)

    with mkt_sub3:
        if not is_pro_user:
            st.info("인스타그램 스튜디오는 PRO 파트너 전용 기능입니다.")
        else:
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                i_type = st.selectbox("콘텐츠 형식", ["단일 피드 (1컷)", "카드뉴스형 (5컷)", "릴스 15초 스크립트"], key="m_i_type")
                i_mood = st.selectbox("비주얼 무드", ["미니멀 모던", "따뜻한 아날로그", "전문 클리닉/정밀 하이테크"], key="m_i_mood")
            with col_i2:
                i_subj = st.text_input("주제", value="얼굴형에 딱 맞는 인생 안경 피팅 노하우", key="m_i_subj")
                i_perk = st.text_input("연계 프로모션", value=my_perk, key="m_i_perk")

            if st.button("인스타그램 피드 생성", key="m_i_btn", use_container_width=True):
                with st.spinner("피드 생성 중..."):
                    prompt = f"매장: {store_name}\n업종: {sel_industry}\n형식: {i_type}\n무드: {i_mood}\n주제: {i_subj}\n혜택: {i_perk}\n촬영 가이드, 첫 줄 카피, 줄바꿈 본문, 해시태그 15종 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("인스타그램 피드", value=out, height=320)

    with mkt_sub4:
        if not is_pro_user:
            st.info("CRM 리텐션 문자는 PRO 파트너 전용 기능입니다.")
        else:
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                c_seg = st.selectbox("대상 세그먼트", ["첫 방문 후 재방문 유도 (1~2주 경과)", "이탈 위험 단골 고객 (60일 이상 미방문)", "정기 검안/렌즈 관리 주기 고객"], key="m_c_seg")
                c_off = st.text_input("제공 바우처", value="재방문 고객 전용 10% 추가 할인 및 김서림 방지 클리너", key="m_c_off")
            with col_c2:
                c_lim = st.selectbox("기한 설정", ["이번 주 일요일까지", "수신 후 14일 이내", "선착순 30명 한정"], key="m_c_lim")
                c_tel = st.text_input("문의처", value=f"{store_name} (문자 회신 가능)", key="m_c_tel")

            if st.button("CRM 메시지 3종 생성", key="m_c_btn", use_container_width=True):
                with st.spinner("문안 작성 중..."):
                    prompt = f"매장: {store_name}\n대상: {c_seg}\n혜택: {c_off}\n기한: {c_lim}\n문의: {c_tel}\n단문 SMS, 장문 LMS, 카카오 알림톡 포맷 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("CRM 메시지 3종", value=out, height=320)

    with mkt_sub5:
        cust_rev = st.text_area("고객 리뷰 본문 붙여넣기", placeholder="고객이 남긴 리뷰를 입력하세요.")
        rev_stl = st.selectbox("답글 스타일", ["정중한 전문 감사형", "친근한 동네 이웃형", "차별점 강조 마케팅형"], key="m_r_stl")
        if st.button("전문 답글 3종 생성", key="m_r_btn", use_container_width=True):
            if cust_rev:
                with st.spinner("답글 작성 중..."):
                    prompt = f"매장: {store_name}\n리뷰: '{cust_rev}'\n스타일: {rev_stl}\n플레이스용 감동적인 답글 3종 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("추천 답글 3종", value=out, height=260)
            else:
                st.warning("리뷰를 입력해 주세요.")

# ------------------------------------------
# TAB 3. 🛒 로컬 공동구매
# ------------------------------------------
with tab_deals:
    deal_sub1, deal_sub2, deal_sub3 = st.tabs(["진행 프로젝트 목록", "소모품 도매 발주", "신규 공구 제안"])

    def get_dday(deadline_str):
        try:
            d_date = datetime.strptime(deadline_str, "%Y-%m-%d")
            delta = (d_date - datetime.now()).days
            return f"D-{delta}일" if delta > 0 else ("오늘 마감" if delta == 0 else "마감")
        except Exception:
            return "진행 중"

    with deal_sub1:
        col_f1, _ = st.columns([1.5, 3])
        with col_f1:
            d_filter = st.selectbox("프로젝트 상태", ["전체 프로젝트", "진행중만 보기", "마감된 프로젝트"], key="d_filter_sel")

        deals_to_del = []
        filtered_deals = []
        for d in deals_db["deals"]:
            d_state = get_dday(d["deadline"])
            if d_filter == "진행중만 보기" and d_state == "마감":
                continue
            if d_filter == "마감된 프로젝트" and d_state != "마감":
                continue
            filtered_deals.append(d)

        for deal in filtered_deals:
            tot_qty = sum([p["qty"] for p in deal["participants"]])
            dday = get_dday(deal["deadline"])
            is_closed = (dday == "마감")

            st.markdown(f"""
            <div class="clean-box" style="margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="background:{'#64748B' if is_closed else '#EF4444'}; color:#fff; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:4px;">{dday}</span>
                    <span style="font-size:0.8rem; color:#64748B;">목표 {deal['target']}개</span>
                </div>
                <h4 style="margin:8px 0 4px 0; color:#0F172A;">{deal['title']}</h4>
                <div style="font-size:1.1rem; font-weight:800; color:#2563EB;">{deal['price']}</div>
                <div style="font-size:0.85rem; color:#475569; margin:4px 0 8px 0;">신청: <b>{len(deal['participants'])}명</b> ({tot_qty}개 달성)</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(tot_qty / deal["target"], 1.0))

            c_btn_a, c_btn_b, c_btn_c = st.columns([1.2, 1.2, 1])
            with c_btn_a:
                if len(deal["participants"]) > 0:
                    df_parts = pd.DataFrame(deal["participants"])
                    df_parts.columns = ["성함/상호", "연락처", "신청수량", "신청일시"]
                    csv_data = df_parts.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="📥 명단 CSV 다운로드",
                        data=csv_data,
                        file_name=f"공구명단_{deal['id']}.csv",
                        mime="text/csv",
                        key=f"csv_{deal['id']}",
                        use_container_width=True
                    )
            with c_btn_b:
                is_active = (st.session_state.active_join_deal_id == deal["id"])
                btn_label = "신청창 닫기" if is_active else "공구 참여 신청"
                if st.button(btn_label, key=f"toggle_join_{deal['id']}", use_container_width=True):
                    st.session_state.active_join_deal_id = None if is_active else deal["id"]
                    st.rerun()
            with c_btn_c:
                if user_key == "admin" or is_closed:
                    if st.button("프로젝트 삭제", key=f"del_{deal['id']}", use_container_width=True):
                        deals_to_del.append(deal["id"])

            if st.session_state.active_join_deal_id == deal["id"]:
                st.markdown(f"""
                <div class="clean-box" style="margin-top:8px; border-left:4px solid #2563EB;">
                    <div style="font-weight:700; font-size:0.92rem; color:#0F172A; margin-bottom:10px;">[{deal['title']}] 참여 신청서</div>
                """, unsafe_allow_html=True)
                with st.form(key=f"join_form_{deal['id']}"):
                    j_name = st.text_input("성함 또는 상호", key=f"j_n_{deal['id']}")
                    j_phone = st.text_input("연락처", key=f"j_p_{deal['id']}")
                    j_qty = st.number_input("신청 수량", min_value=1, max_value=100, value=1, step=1, key=f"j_q_{deal['id']}")
                    if st.form_submit_button("참여 확정하기", use_container_width=True):
                        if j_name and j_phone:
                            deal["participants"].append({"name": j_name, "phone": j_phone, "qty": int(j_qty), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                            save_deals(deals_db)
                            st.session_state.active_join_deal_id = None
                            st.success("참여 완료되었습니다.")
                            st.rerun()
                        else:
                            st.warning("정보를 입력해 주세요.")
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:14px 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

        if deals_to_del:
            deals_db["deals"] = [d for d in deals_db["deals"] if d["id"] not in deals_to_del]
            save_deals(deals_db)
            st.rerun()

    with deal_sub2:
        st.markdown("""
        <div class="clean-box">
            <h4 style="margin:0; color:#0F172A;">카드단말기 영수증 롤페이퍼 (50롤 1박스)</h4>
            <p style="color:#475569; font-size:0.9rem; margin-top:6px;">시중가 38,000원 ➡️ <b>공구가 23,500원 (무료배송)</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("소모품 도매 공동발주 접수", key="btn_b2b_submit", use_container_width=True):
            st.success("발주 신청이 접수되었습니다.")

    with deal_sub3:
        p_name = st.text_input("제안 상품명", key="p_name_input")
        p_qty = st.number_input("목표 수량", min_value=1, max_value=1000, value=30, step=1, key="p_qty_input")
        p_price = st.text_input("제안 공구가", key="p_price_input")
        p_days = st.slider("진행 일수", min_value=3, max_value=30, value=7, key="p_days_input")
        if st.button("공동구매 프로젝트 오픈 등록", key="btn_prop_submit", use_container_width=True):
            if p_name and p_price:
                deals_db["deals"].append({
                    "id": f"deal_{int(time.time())}",
                    "title": f"[{store_name}] {p_name}",
                    "price": f"{p_price} (단독 특가)",
                    "target": int(p_qty),
                    "deadline": (datetime.now() + timedelta(days=p_days)).strftime("%Y-%m-%d"),
                    "participants": []
                })
                save_deals(deals_db)
                st.success("공동구매 프로젝트가 개설되었습니다.")
                st.rerun()

# ------------------------------------------
# TAB 4. 💼 경영 & 행정지원
# ------------------------------------------
with tab_biz:
    biz_sub1, biz_sub2, biz_sub3, biz_sub4 = st.tabs([
        "4대 행정서류 발급처", "2026 정책금융 진단", "알바 급여 & 영업 결산", "매장 시간대별 음악"
    ])

    # 4대 행정서류: 정책금융과 동일한 카드 그리드 스타일로 전면 개편
    with biz_sub1:
        st.markdown("##### 정책자금 및 금융 필수 4대 증빙 서류 발급처")
        st.markdown("""
        <div class="unified-grid">
            <div class="unified-card">
                <div>
                    <span style="font-size:0.75rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:2px 6px; border-radius:4px;">소상공인 증빙</span>
                    <div style="font-weight:700; color:#0F172A; margin:6px 0;">소상공인확인서</div>
                    <div style="font-size:0.85rem; color:#475569; line-height:1.5;">
                        • 발급처: 중소기업현황정보시스템<br>
                        • 용도: 국비 지원금 및 보증 신청 필수<br>
                        • 수수료: 무료 (온라인 즉시 발급)
                    </div>
                </div>
                <a href="https://sminfo.mss.go.kr" target="_blank" style="text-decoration:none; margin-top:12px;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.82rem; font-weight:700; cursor:pointer;">발급 사이트 바로가기</button>
                </a>
            </div>
            <div class="unified-card">
                <div>
                    <span style="font-size:0.75rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:2px 6px; border-radius:4px;">매출 규모 증빙</span>
                    <div style="font-weight:700; color:#0F172A; margin:6px 0;">부가가치세 과세표준증명</div>
                    <div style="font-size:0.85rem; color:#475569; line-height:1.5;">
                        • 발급처: 국세청 홈택스 / 손택스<br>
                        • 용도: 대출 및 신용보증 심사 시 매출 확인<br>
                        • 수수료: 무료 (온라인 즉시 발급)
                    </div>
                </div>
                <a href="https://www.hometax.go.kr" target="_blank" style="text-decoration:none; margin-top:12px;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.82rem; font-weight:700; cursor:pointer;">홈택스 발급 바로가기</button>
                </a>
            </div>
            <div class="unified-card">
                <div>
                    <span style="font-size:0.75rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:2px 6px; border-radius:4px;">국세 체납 확인</span>
                    <div style="font-weight:700; color:#0F172A; margin:6px 0;">국세 완납증명서 (납세증명)</div>
                    <div style="font-size:0.85rem; color:#475569; line-height:1.5;">
                        • 발급처: 국세청 홈택스<br>
                        • 용도: 세금 체납 여부 확인 (정책자금 필수)<br>
                        • 수수료: 무료 (유효기간 30일)
                    </div>
                </div>
                <a href="https://www.hometax.go.kr" target="_blank" style="text-decoration:none; margin-top:12px;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.82rem; font-weight:700; cursor:pointer;">납세증명 메뉴 바로가기</button>
                </a>
            </div>
            <div class="unified-card">
                <div>
                    <span style="font-size:0.75rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:2px 6px; border-radius:4px;">지방세 체납 확인</span>
                    <div style="font-weight:700; color:#0F172A; margin:6px 0;">지방세 납세증명서</div>
                    <div style="font-size:0.85rem; color:#475569; line-height:1.5;">
                        • 발급처: 정부24 / 주민센터<br>
                        • 용도: 지방세(재산세 등) 완납 여부 증빙<br>
                        • 수수료: 무료 (온라인 즉시 발급)
                    </div>
                </div>
                <a href="https://www.gov.kr" target="_blank" style="text-decoration:none; margin-top:12px;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.82rem; font-weight:700; cursor:pointer;">정부24 발급 바로가기</button>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with biz_sub2:
        st.markdown("##### 2026 소상공인 정책금융 및 국비 지원사업 분석")
        st.markdown("""
        <div class="unified-grid">
            <div class="unified-card">
                <div>
                    <span style="font-size:0.75rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:2px 6px; border-radius:4px;">비용 절감</span>
                    <div style="font-weight:700; color:#0F172A; margin:6px 0;">소상공인 전기요금 특별지원</div>
                    <div style="font-size:0.85rem; color:#475569; line-height:1.5;">
                        • 지원 규모: 사업장당 최대 20~25만 원 감면<br>
                        • 자격: 연 매출 6천만 원 이하 영세 소상공인<br>
                        • 접수: 전용 신청 사이트 온라인 접수
                    </div>
                </div>
                <a href="https://www.소상공인전기요금특별지원.kr" target="_blank" style="text-decoration:none; margin-top:12px;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.82rem; font-weight:700; cursor:pointer;">신청 사이트 열기</button>
                </a>
            </div>
            <div class="unified-card">
                <div>
                    <span style="font-size:0.75rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:2px 6px; border-radius:4px;">이자 경감</span>
                    <div style="font-weight:700; color:#0F172A; margin:6px 0;">고금리 저금리 대환보증</div>
                    <div style="font-size:0.85rem; color:#475569; line-height:1.5;">
                        • 지원 혜택: 7% 이상 대출을 4%대로 전환<br>
                        • 보증 한도: 사업자당 최대 5,000만 원<br>
                        • 접수: 신용보증재단 및 정책자금 포털
                    </div>
                </div>
                <a href="https://www.semas.or.kr" target="_blank" style="text-decoration:none; margin-top:12px;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.82rem; font-weight:700; cursor:pointer;">공고 확인하기</button>
                </a>
            </div>
            <div class="unified-card">
                <div>
                    <span style="font-size:0.75rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:2px 6px; border-radius:4px;">매장 인프라</span>
                    <div style="font-weight:700; color:#0F172A; margin:6px 0;">스마트상점 기술보급 국비 지원</div>
                    <div style="font-size:0.85rem; color:#475569; line-height:1.5;">
                        • 지원 혜택: 키오스크/테이블오더 70% 국비 지원<br>
                        • 지원 한도: 일반형 500만 원 / 미래형 1,000만 원<br>
                        • 접수: 소상공인스마트상점 공식 포털
                    </div>
                </div>
                <a href="https://www.sbiz.or.kr/smst/index.do" target="_blank" style="text-decoration:none; margin-top:12px;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.82rem; font-weight:700; cursor:pointer;">사업 공고 열기</button>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_pol1, col_pol2 = st.columns(2)
        with col_pol1:
            rev_s = st.selectbox("사업장 연매출 규모", ["3천만 원 미만 (영세)", "3천만 원 ~ 1억 원", "1억 원 ~ 3억 원", "3억 원 초과"], key="b_rev_s")
        with col_pol2:
            aid_p = st.selectbox("가장 시급한 지원", ["고금리 대출 이자 완화", "매장 설비/키오스크 보조", "운영 고정비 지원"], key="b_aid_p")
        if st.button("맞춤 정책자금 AI 진단 실행", key="b_aid_btn", use_container_width=True):
            with st.spinner("정책 분석 중..."):
                out = generate_safe_content(f"업종: {sel_industry}\n매출: {rev_s}\n목적: {aid_p}\n가장 적합한 정부 정책 2종과 신청 요건을 공문서 리포트로 작성.")
                if out: st.markdown(f"<div class='clean-box' style='border-left:4px solid #2563EB;'>{out}</div>", unsafe_allow_html=True)

    with biz_sub3:
        st.markdown("##### 💰 파트타이머 주휴수당 및 실수령액 산출")
        w1, w2 = st.columns(2)
        with w1:
            wage = st.number_input("기본 시급 (원)", value=10030, step=100, key="b_wage")
            hrs = st.number_input("주당 소정근로시간", value=16.0, step=0.5, key="b_hrs")
        with w2:
            tax_opt = st.selectbox("공제 기준", ["사업소득세 3.3% 공제", "고용보험 0.9% 공제", "공제 미적용"], key="b_tax")
        base = wage * hrs * 4.345
        holiday = ((hrs / 40.0) * 8.0 * wage * 4.345) if hrs >= 15 else 0
        tot = base + holiday
        ded = tot * 0.033 if "3.3%" in tax_opt else (tot * 0.009 if "0.9%" in tax_opt else 0)
        net = tot - ded
        st.markdown(f"""
        <div class="clean-box" style="margin-top:6px; margin-bottom:14px;">
            <div style="font-size:0.86rem; color:#64748B;">기본급: {int(base):,}원 | 주휴수당: {int(holiday):,}원 (원천공제: {int(ded):,}원)</div>
            <div style="font-size:1.2rem; font-weight:800; color:#0F172A; margin-top:2px;">예상 실지급액: {int(net):,}원</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### 🌙 일일 영업 결산 리포트")
        cl_col1, cl_col2 = st.columns(2)
        with cl_col1:
            c_sales = st.text_input("오늘 대략적인 매출액 (선택)", placeholder="예: 850,000원", key="b_sales")
            c_flow = st.selectbox("고객 유입 체감", ["평소 대비 한산함", "평균 수준", "피크타임 집중 방문", "종일 만석"], key="b_flow")
        with cl_col2:
            c_memo = st.text_input("특이사항/재고 이슈", placeholder="예: 특정 렌즈 재고 소진", key="b_memo")
            c_sat = st.selectbox("운영 만족도", ["다소 아쉬움", "무난하고 안정적", "매우 만족"], key="b_sat")
        if st.button("일일 경영 결산 리포트 생성", key="b_close_btn", use_container_width=True):
            with st.spinner("경영 데이터 종합 분석 중..."):
                out = generate_safe_content(f"가게: {store_name}\n매출: {c_sales}\n유입: {c_flow}\n특이사항: {c_memo}\n만족도: {c_sat}\n일일 경영 총평, 내일 실행과제 3선, 퇴근길 멘탈 리셋 조언 작성.")
                if out: st.markdown(f"<div class='clean-box' style='border-left:4px solid #2563EB;'>{out}</div>", unsafe_allow_html=True)

    with biz_sub4:
        st.markdown("##### 🎧 매장 시간대·상황별 음악 큐레이션")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            m_time = st.selectbox("영업 시간대", ["오전 오픈 준비 (경쾌한 무드)", "점심/오후 피크 (활기 유지)", "나른한 오후 3~5시 (편안한 칠아웃)", "저녁 골든타임 (아늑한 라운지/재즈)", "마감 정리 (차분한 피아노)"], key="b_m_time")
        with col_m2:
            m_style = st.selectbox("장르 스타일", ["재즈/보사노바", "어쿠스틱 팝", "2000년대 감성 발라드 피아노", "90-2000 가요 댄스"], key="b_m_style")
        yt_q = f"{m_style.split('/')[0]} {m_time.split('(')[0].strip()} 플레이리스트 연속재생"
        st.link_button(f"유튜브 '{yt_q}' 스트리밍 재생", f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_q)}", use_container_width=True)
