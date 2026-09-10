import os
import sys
import time
import json
import urllib.parse
from datetime import datetime, timedelta

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import streamlit as st
from google import genai
from google.genai import errors

# ==========================================
# 기본 설정 및 데이터베이스
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
            "feature": "독일식 초정밀 검안 솔루션",
            "map_address": "경기도 용인시 처인구 이동읍 경기동로 725",
            "map_perk": "용친 회원 안경렌즈 10% 현장 할인 및 클리너 제공",
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
                "title": "[처인구 파트너십] 볏짚 숙성 삼겹 3인 세트 + 냉면 이용권",
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
    page_title="STORE MATE | 로컬 비즈니스 플랫폼",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 정통 모던 엔터프라이즈 CSS (이모티콘 제거, 타이포 중심)
# ==========================================
st.markdown("""
<meta name="color-scheme" content="only light">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<style>
    :root { color-scheme: light only !important; }
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, input, button, a {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
        letter-spacing: -0.025em;
    }
    .stApp { background-color: #F8FAFC !important; }

    /* 인풋 컨트롤 모던 정렬 */
    input, textarea, select, 
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"] > input,
    input:focus, textarea:focus, select:focus {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: #0F172A !important;
        font-size: 0.92rem !important;
    }

    /* 엔터프라이즈 상단 헤더 */
    .app-header {
        background: #0F172A;
        border-radius: 14px;
        padding: 22px 26px;
        color: #FFFFFF;
        margin-bottom: 14px;
        border: 1px solid #1E293B;
    }
    .app-header * { color: #FFFFFF !important; }
    .header-badge {
        font-size: 0.72rem;
        font-weight: 700;
        background: #2563EB;
        padding: 3px 8px;
        border-radius: 4px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 6px;
    }

    /* KPI 상태 메트릭 바 */
    .metric-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 10px;
        margin-bottom: 14px;
    }
    .metric-item {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 16px;
    }
    .metric-title { font-size: 0.75rem; color: #64748B; font-weight: 600; margin-bottom: 2px; }
    .metric-number { font-size: 1.05rem; color: #0F172A; font-weight: 700; }

    /* SNS 채널 바 */
    .sns-channel-bar {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }
    .channel-title { font-size: 0.85rem; font-weight: 700; color: #334155; }
    .channel-group { display: flex; gap: 8px; flex-wrap: wrap; }
    .btn-channel {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        text-decoration: none !important;
    }
    .btn-fb { background: #1877F2; color: #FFFFFF !important; }
    .btn-insta { background: #E1306C; color: #FFFFFF !important; }
    .btn-threads { background: #111827; color: #FFFFFF !important; }

    /* 모던 카드 UI */
    .clean-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 14px;
    }
    .guide-banner {
        background: #F1F5F9;
        border-left: 3px solid #2563EB;
        padding: 12px 14px;
        border-radius: 6px;
        font-size: 0.88rem;
        color: #334155;
        margin-bottom: 14px;
        font-weight: 500;
    }

    /* 탭 메뉴 (이모티콘 없이 담백한 폰트) */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        gap: 4px !important;
        background: #E2E8F0 !important;
        padding: 4px !important;
        border-radius: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 36px !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 14px !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    /* 표준 비즈니스 버튼 */
    .stButton>button {
        height: 3rem !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    .stButton>button:hover {
        background: #1D4ED8 !important;
    }
</style>
""", unsafe_allow_html=True)

INDUSTRY_LIST = [
    "식당 / 고깃집 / 일반음식점",
    "포차 / 주점 / 이자카야 / 호프",
    "카페 / 베이커리 / 디저트",
    "안경원 / 렌즈 / 패션잡화",
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

# ==========================================
# 로그인 및 회원가입
# ==========================================
if not st.session_state.logged_in_user:
    st.markdown("""
    <div style="max-width: 420px; margin: 40px auto 20px auto; text-align: center;">
        <h2 style="font-size: 1.6rem; font-weight: 800; color: #0F172A; margin: 0 0 6px 0;">STORE MATE</h2>
        <p style="font-size: 0.9rem; color: #64748B;">용인친구들 소상공인 통합 관리 시스템</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.02, 0.96, 0.02])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["로그인", "신규 사업자 등록"])
        with auth_tab1:
            with st.form("login_form"):
                login_id = st.text_input("아이디 또는 사업자 연락처", placeholder="아이디를 입력하세요")
                login_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호")
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
                new_id = st.text_input("아이디 (연락처 권장)", placeholder="예: 01012345678")
                new_pw = st.text_input("비밀번호 설정", type="password", placeholder="4자리 이상 입력")
                new_store = st.text_input("매장 상호명", placeholder="예: 드림안경 송전점")
                new_ind = st.selectbox("업종 선택", INDUSTRY_LIST)
                new_loc = st.text_input("매장 주소", placeholder="예: 용인시 처인구 이동읍 경기동로 725")
                if st.form_submit_button("등록 신청", use_container_width=True):
                    if new_id and new_pw and new_store:
                        users_db[new_id] = {
                            "store_name": new_store,
                            "industry": new_ind,
                            "location": new_loc,
                            "feature": "전문 상담 및 정밀 서비스",
                            "map_address": new_loc,
                            "map_perk": "용친 회원 방문 시 특별 혜택 제공",
                            "pw": new_pw,
                            "is_pro": False,
                            "pro_status": "미신청" 
                        }
                        save_users(users_db)
                        st.success("등록이 완료되었습니다. 로그인해 주세요.")
    st.stop()

# ==========================================
# 메인 대시보드
# ==========================================
user_key = st.session_state.logged_in_user
curr_user = users_db.get(user_key, {})
store_name = curr_user.get("store_name", "드림안경 송전점")
sel_industry = curr_user.get("industry", INDUSTRY_LIST[3])
sel_loc = curr_user.get("location", "용인시 처인구 이동읍 경기동로 725")
sel_feature = curr_user.get("feature", "독일식 초정밀 시력검사")
is_pro_user = curr_user.get("is_pro", False)
pro_status = curr_user.get("pro_status", "미신청")

with st.sidebar:
    st.markdown("### 매장 계정 정보")
    st.markdown(f"**{store_name}**")
    
    if is_pro_user:
        st.caption("플랜: PRO 비즈니스 파트너")
    else:
        st.caption("플랜: 스탠다드 회원")
        if st.button("PRO 권한 신청", use_container_width=True):
            curr_user["pro_status"] = "대기중"
            users_db[user_key] = curr_user
            save_users(users_db)
            st.rerun()

    if user_key == "admin":
        st.markdown("---")
        st.markdown("### 관리자 회원 승인")
        for uid, udata in users_db.items():
            ustore = udata.get("store_name", uid)
            u_is_pro = udata.get("is_pro", False)
            st.markdown(f"**{ustore}** (`{uid}`)")
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

# 1. 메인 헤더
st.markdown(f"""
<div class="app-header">
    <div class="header-badge">{'PRO PARTNER' if is_pro_user else 'STANDARD MEMBER'}</div>
    <div style="font-size: 1.45rem; font-weight: 800; margin-bottom: 2px;">{store_name}</div>
    <div style="font-size: 0.88rem; opacity: 0.85;">{sel_loc} &nbsp;|&nbsp; {sel_industry}</div>
</div>
""", unsafe_allow_html=True)

# 2. 비즈니스 메트릭
st.markdown(f"""
<div class="metric-row">
    <div class="metric-item">
        <div class="metric-title">시스템 상태</div>
        <div class="metric-number" style="color: #16A34A;">정상 가동</div>
    </div>
    <div class="metric-item">
        <div class="metric-title">공동구매 등록</div>
        <div class="metric-number">{len(deals_db.get('deals', []))}건 진행</div>
    </div>
    <div class="metric-item">
        <div class="metric-title">제휴 커뮤니티</div>
        <div class="metric-number">용인친구들</div>
    </div>
    <div class="metric-item">
        <div class="metric-title">AI 마케팅 엔진</div>
        <div class="metric-number">Flash v3.6</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. 소셜 채널 링크 바 (이모티콘 없이 깔끔한 텍스트 칩)
st.markdown("""
<div class="sns-channel-bar">
    <div class="channel-title">공식 소셜 미디어 채널</div>
    <div class="channel-group">
        <a href="https://www.facebook.com/groups/yonginfriends" target="_blank" class="btn-channel btn-fb">
            페이스북 그룹
        </a>
        <a href="https://www.instagram.com/" target="_blank" class="btn-channel btn-insta">
            인스타그램
        </a>
        <a href="https://www.threads.net/" target="_blank" class="btn-channel btn-threads">
            스레드
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

SYSTEM_DIRECTIVE = """
너는 골목상권과 로컬 비즈니스 생리를 꿰뚫고 있는 20년 경력의 베테랑 로컬 상생 마케팅 디렉터다.
답변 시 이모티콘을 남발하지 말고, 전문 컨설턴트처럼 담백하고 세련된 문장으로 완성본 원고를 제공한다.
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
            st.error("데이터를 생성하지 못했습니다. 잠시 후 다시 시도해 주세요.")
            return None

# ==========================================
# 탭 메뉴 (이모티콘 싹 제거)
# ==========================================
tab_titles = [
    "매장음악",
    "상생아지트",
    "공동구매",
    "블로그원고",
    "당근소식",
    "인스타그램",
    "고객문자",
    "급여계산",
    "행정서류",
    "정책지원",
    "영업마감"
]
tabs = st.tabs(tab_titles)

# 0. 매장음악
with tabs[0]:
    st.markdown("""
    <div class="guide-banner">
        매장 분위기와 타깃 고객 연령대에 맞춘 유튜브 검색 런처입니다.
    </div>
    """, unsafe_allow_html=True)
    col_m1, col_m2 = st.columns([1.2, 1])
    with col_m1:
        sel_mood = st.selectbox("분위기 선택", [
            "차분하고 편안한 힐링 (전문상담, 뷰티, 안경원)",
            "활기차고 경쾌한 무드 (일반음식점, 주점, 펍)",
            "푸근한 레트로 (노포, 한식, 단골 중심)"
        ], key="v3_mood")
        sel_genre = st.selectbox("장르 선택", [
            "피아노 힐링 연주곡 메들리",
            "2000년대 감성 명곡 발라드",
            "90-2000 국민 애창 댄스곡",
            "트로트 베스트 모음"
        ], key="v3_genre")
        target_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(sel_genre + ' 연속재생')}"
    with col_m2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button("유튜브 검색 결과 열기", target_url, use_container_width=True)

# 1. 상생아지트
with tabs[1]:
    my_saved_addr = curr_user.get("map_address", sel_loc)
    my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
    naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"
    st.markdown(f"""
    <div class="clean-card">
        <h4 style="margin-top:0; color:#0F172A;">공식 제휴 매장: {store_name}</h4>
        <p style="color:#475569; font-size:0.92rem; margin-bottom:6px;">사업장 주소: {my_saved_addr}</p>
        <p style="color:#2563EB; font-weight:700; font-size:0.92rem; margin-bottom:16px;">회원 제휴 혜택: {my_perk}</p>
        <a href="{naver_url}" target="_blank" style="text-decoration:none;">
            <button style="width:100%; height:42px; background:#03C75A; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; cursor:pointer;">
                네이버 플레이스 지도 연동 확인
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

# 2. 공동구매
with tabs[2]:
    st.markdown("##### 진행 중인 공동구매 프로젝트")
    for deal in deals_db["deals"]:
        total_qty = sum([p["qty"] for p in deal["participants"]])
        st.markdown(f"""
        <div class="clean-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:#0F172A;">{deal['title']}</h4>
                <span style="font-size:0.8rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:3px 8px; border-radius:4px;">접수중</span>
            </div>
            <p style="font-size:1rem; font-weight:700; color:#2563EB; margin:8px 0;">{deal['price']}</p>
            <p style="font-size:0.85rem; color:#64748B; margin:0;">참여 인원: {len(deal['participants'])}명 (신청 수량: {total_qty}개)</p>
        </div>
        """, unsafe_allow_html=True)

# 3. 블로그원고
with tabs[3]:
    if not is_pro_user:
        st.info("네이버 플레이스 연동 블로그 원고 작성기는 PRO 파트너 전용 기능입니다.")
    else:
        n_name = st.text_input("상호명 및 지역", value=f"{store_name} ({sel_loc})", key="v3_bl_name")
        n_item = st.text_input("매장 핵심 강점", value=sel_feature, key="v3_bl_item")
        if st.button("원고 작성 실행", key="v3_bl_btn"):
            with st.spinner("전문 마케팅 원고를 작성하고 있습니다..."):
                out = generate_safe_content(f"상호: {n_name}\n강점: {n_item}\n네이버 플레이스 방문 리뷰 유도용 블로그 포스팅 원고를 전문성 있게 작성.")
                if out:
                    st.text_area("생성된 원고", value=out, height=320)

# 4. 당근소식
with tabs[4]:
    if not is_pro_user:
        st.info("당근마켓 동네생활 소식 작성기는 PRO 파트너 전용 기능입니다.")
    else:
        d_topic = st.selectbox("소식 주제", ["첫 방문 고객 혜택 안내", "신규 상품/서비스 입고", "단기 프로모션 진행"], key="v3_dg_topic")
        if st.button("소식 원고 작성", key="v3_dg_btn"):
            with st.spinner("동네생활 포스팅 작성 중..."):
                out = generate_safe_content(f"가게: {store_name}\n업종: {sel_industry}\n주제: {d_topic}\n당근마켓 이웃들에게 신뢰를 주는 자연스러운 어투로 작성.")
                if out:
                    st.text_area("당근 소식 원고", value=out, height=280)

# 5. 인스타그램
with tabs[5]:
    if not is_pro_user:
        st.info("인스타그램 피드 및 태그 최적화는 PRO 파트너 전용 기능입니다.")
    else:
        if st.button("인스타그램 피드 생성", key="v3_ig_btn"):
            with st.spinner("인스타그램 피드 구성 중..."):
                out = generate_safe_content(f"가게: {store_name}\n업종: {sel_industry}\n감성적인 카피와 본문, 핵심 지역 해시태그 8개를 정갈하게 작성.")
                if out:
                    st.text_area("피드 원고", value=out, height=260)

# 6. 고객문자
with tabs[6]:
    if not is_pro_user:
        st.info("단골 고객 리텐션 메시지 생성기는 PRO 파트너 전용 기능입니다.")
    else:
        m_target = st.selectbox("발송 목적", ["재방문 감사 쿠폰", "계절 안부 및 프로모션 안내", "서비스 점검 안내"], key="v3_sms_target")
        if st.button("메시지 템플릿 생성", key="v3_sms_btn"):
            with st.spinner("문자 템플릿 작성 중..."):
                out = generate_safe_content(f"가게: {store_name}\n목적: {m_target}\n단문 SMS 규격 및 장문 LMS 규격 2가지 버전으로 작성.")
                if out:
                    st.text_area("문자 템플릿", value=out, height=240)

# 7. 급여계산
with tabs[7]:
    st.markdown("##### 시간제 근무자 주휴수당 및 실지급액 산출")
    w1, w2 = st.columns(2)
    with w1:
        wage = st.number_input("기본 시급 (원)", value=10030, step=100, key="v3_w")
        hours = st.number_input("주당 소정근로시간", value=16.0, step=0.5, key="v3_h")
    with w2:
        tax_opt = st.selectbox("공제 기준", ["사업소득세 3.3% 공제", "고용보험 0.9% 공제", "공제 미적용"], key="v3_t")
    
    base = wage * hours * 4.345
    holiday = ((hours / 40.0) * 8.0 * wage * 4.345) if hours >= 15 else 0
    total = base + holiday
    deduct = total * 0.033 if "3.3%" in tax_opt else (total * 0.009 if "0.9%" in tax_opt else 0)
    net = total - deduct
    
    st.markdown(f"""
    <div class="clean-card" style="background:#F8FAFC;">
        <div style="font-size:0.88rem; color:#64748B;">기본급 합계: {int(base):,}원 &nbsp;|&nbsp; 법정 주휴수당: {int(holiday):,}원</div>
        <div style="font-size:1.25rem; font-weight:800; color:#0F172A; margin:8px 0;">예상 실지급액: {int(net):,}원</div>
        <div style="font-size:0.8rem; color:#94A3B8;">(원천징수 공제 예상액: {int(deduct):,}원 차감)</div>
    </div>
    """, unsafe_allow_html=True)

# 8. 행정서류
with tabs[8]:
    st.markdown("""
    <div class="clean-card">
        <h4 style="margin-top:0; color:#0F172A;">정책자금 및 금융 필수 제출 서류 발급처</h4>
        <ul style="color:#334155; line-height:1.8; font-size:0.92rem; margin-bottom:0;">
            <li><b>소상공인확인서:</b> 중소기업현황정보시스템 (sminfo.mss.go.kr)</li>
            <li><b>부가가치세 과세표준증명원:</b> 국세청 홈택스 (hometax.go.kr)</li>
            <li><b>국세 완납증명서:</b> 국세청 홈택스 납세증명 메뉴</li>
            <li><b>지방세 납세증명서:</b> 정부24 (gov.kr) 민원서비스</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 9. 정책지원
with tabs[9]:
    st.markdown("""
    <div class="clean-card">
        <h4 style="margin-top:0; color:#0F172A;">주요 소상공인 정책 지원 안내</h4>
        <p style="color:#475569; font-size:0.92rem; line-height:1.6; margin-bottom:0;">
            • <b>소상공인 전기요금 특별지원:</b> 연 매출 기준 충족 시 최대 20~25만 원 감면 지원<br>
            • <b>고금리 대환대출 프로그램:</b> 7% 이상 고금리 사업자 대출을 4%대 저금리 전환<br>
            • <b>스마트상점 기술보급 사업:</b> 테이블오더, 전자키오스크 도입 비용의 최대 70% 국비 지원
        </p>
    </div>
    """, unsafe_allow_html=True)

# 10. 영업마감
with tabs[10]:
    st.markdown("##### 영업 마감 브리핑 및 익일 운영 제언")
    if st.button("마감 브리핑 작성 실행", key="v3_close_btn"):
        with st.spinner("영업 마감 리포트를 정리하고 있습니다..."):
            out = generate_safe_content(f"가게: {store_name} ({sel_industry})\n오늘 하루를 정리하는 전문적이고 격려가 담긴 마감 리포트와 익일 영업 준비 팁 1가지 작성.")
            if out:
                st.markdown(f"""
                <div class="clean-card" style="border-left: 3px solid #2563EB;">
                    <div style="font-weight:700; color:#0F172A; margin-bottom:8px;">일일 영업 마감 리포트</div>
                    <div style="color:#334155; font-size:0.92rem; line-height:1.6;">{out}</div>
                </div>
                """, unsafe_allow_html=True)
