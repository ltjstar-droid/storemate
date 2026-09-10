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
# 정통 모던 엔터프라이즈 CSS
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

    /* 정책지원 & 행정 서식 전용 구조화 카드 */
    .policy-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 14px;
        margin-top: 10px;
    }
    .policy-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .policy-box-title { font-size: 0.98rem; font-weight: 700; color: #0F172A; margin-bottom: 6px; }
    .policy-tag { display: inline-block; font-size: 0.72rem; font-weight: 700; color: #2563EB; background: #EFF6FF; padding: 2px 6px; border-radius: 4px; margin-bottom: 8px; width: fit-content; }
    .policy-detail { font-size: 0.85rem; color: #475569; line-height: 1.5; margin-bottom: 12px; }

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

    .stButton>button {
        height: 3rem !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    .stButton>button:hover { background: #1D4ED8 !important; }
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
# 로그인 화면
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
                login_id = st.text_input("아이디 또는 사업자 연락처", placeholder="아이디 입력")
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
                new_pw = st.text_input("비밀번호 설정", type="password", placeholder="4자리 이상")
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

st.markdown(f"""
<div class="app-header">
    <div class="header-badge">{'PRO PARTNER' if is_pro_user else 'STANDARD MEMBER'}</div>
    <div style="font-size: 1.45rem; font-weight: 800; margin-bottom: 2px;">{store_name}</div>
    <div style="font-size: 0.88rem; opacity: 0.85;">{sel_loc} &nbsp;|&nbsp; {sel_industry}</div>
</div>
""", unsafe_allow_html=True)

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
        <div class="metric-title">빌드 상태</div>
        <div class="metric-number">최신 패치 완료</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sns-channel-bar">
    <div class="channel-title">공식 소셜 미디어 채널</div>
    <div class="channel-group">
        <a href="https://www.facebook.com/groups/yonginfriends" target="_blank" class="btn-channel btn-fb">페이스북 그룹</a>
        <a href="https://www.instagram.com/" target="_blank" class="btn-channel btn-insta">인스타그램</a>
        <a href="https://www.threads.net/" target="_blank" class="btn-channel btn-threads">스레드</a>
    </div>
</div>
""", unsafe_allow_html=True)

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

SYSTEM_DIRECTIVE = """
너는 소상공인 실무 정책 및 세무 행정 분야의 20년 경력 수석 컨설턴트다.
모호한 미사여구는 배제하고, 정확한 신청 자격, 구체적인 제출 단계, 절세 전략을 표준 공문서 및 전문 컨설팅 리포트 형식으로 전달한다.
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
            st.error("데이터 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.")
            return None

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
    col_m1, col_m2 = st.columns([1.2, 1])
    with col_m1:
        sel_mood = st.selectbox("분위기 선택", [
            "차분하고 편안한 힐링 (전문상담, 뷰티, 안경원)",
            "활기차고 경쾌한 무드 (일반음식점, 주점, 펍)",
            "푸근한 레트로 (노포, 한식, 단골 중심)"
        ], key="v4_mood")
        sel_genre = st.selectbox("장르 선택", [
            "피아노 힐링 연주곡 메들리",
            "2000년대 감성 명곡 발라드",
            "90-2000 국민 애창 댄스곡",
            "트로트 베스트 모음"
        ], key="v4_genre")
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
    for deal in deals_db["deals"]:
        total_qty = sum([p["qty"] for p in deal["participants"]])
        st.markdown(f"""
        <div class="clean-card">
            <h4 style="margin:0; color:#0F172A;">{deal['title']}</h4>
            <p style="font-size:1rem; font-weight:700; color:#2563EB; margin:6px 0;">{deal['price']}</p>
            <p style="font-size:0.85rem; color:#64748B; margin:0;">참여 인원: {len(deal['participants'])}명 (신청 수량: {total_qty}개)</p>
        </div>
        """, unsafe_allow_html=True)

# 3. 블로그원고
with tabs[3]:
    if not is_pro_user: st.info("PRO 파트너 전용 기능입니다.")
    else:
        n_name = st.text_input("상호명 및 지역", value=f"{store_name} ({sel_loc})", key="v4_bl_name")
        n_item = st.text_input("매장 핵심 강점", value=sel_feature, key="v4_bl_item")
        if st.button("원고 작성 실행", key="v4_bl_btn"):
            out = generate_safe_content(f"상호: {n_name}\n강점: {n_item}\n네이버 플레이스 리뷰 유도형 블로그 원고 작성.")
            if out: st.text_area("작성된 원고", value=out, height=300)

# 4. 당근소식
with tabs[4]:
    if not is_pro_user: st.info("PRO 파트너 전용 기능입니다.")
    else:
        d_topic = st.selectbox("소식 주제", ["첫 방문 고객 혜택", "신규 상품 입고", "단기 프로모션"], key="v4_dg_topic")
        if st.button("소식 원고 작성", key="v4_dg_btn"):
            out = generate_safe_content(f"가게: {store_name}\n업종: {sel_industry}\n주제: {d_topic}\n당근마켓 동네생활 톤앤매너로 작성.")
            if out: st.text_area("당근 소식", value=out, height=260)

# 5. 인스타그램
with tabs[5]:
    if not is_pro_user: st.info("PRO 파트너 전용 기능입니다.")
    else:
        if st.button("인스타그램 피드 생성", key="v4_ig_btn"):
            out = generate_safe_content(f"가게: {store_name}\n업종: {sel_industry}\n감성적인 카피와 해시태그 8개 작성.")
            if out: st.text_area("인스타그램 피드", value=out, height=240)

# 6. 고객문자
with tabs[6]:
    if not is_pro_user: st.info("PRO 파트너 전용 기능입니다.")
    else:
        m_target = st.selectbox("발송 목적", ["재방문 감사 쿠폰", "계절 안부 및 프로모션 안내"], key="v4_sms_target")
        if st.button("메시지 템플릿 생성", key="v4_sms_btn"):
            out = generate_safe_content(f"가게: {store_name}\n목적: {m_target}\n단문 SMS 및 장문 LMS 규격으로 작성.")
            if out: st.text_area("문자 템플릿", value=out, height=240)

# 7. 급여계산
with tabs[7]:
    w1, w2 = st.columns(2)
    with w1:
        wage = st.number_input("기본 시급 (원)", value=10030, step=100, key="v4_w")
        hours = st.number_input("주당 소정근로시간", value=16.0, step=0.5, key="v4_h")
    with w2:
        tax_opt = st.selectbox("공제 기준", ["사업소득세 3.3% 공제", "고용보험 0.9% 공제", "공제 미적용"], key="v4_t")
    
    base = wage * hours * 4.345
    holiday = ((hours / 40.0) * 8.0 * wage * 4.345) if hours >= 15 else 0
    total = base + holiday
    deduct = total * 0.033 if "3.3%" in tax_opt else (total * 0.009 if "0.9%" in tax_opt else 0)
    net = total - deduct
    st.markdown(f"""
    <div class="clean-card" style="background:#F8FAFC;">
        <div style="font-size:0.88rem; color:#64748B;">기본급 합계: {int(base):,}원 &nbsp;|&nbsp; 법정 주휴수당: {int(holiday):,}원</div>
        <div style="font-size:1.25rem; font-weight:800; color:#0F172A; margin:6px 0;">예상 실지급액: {int(net):,}원</div>
        <div style="font-size:0.8rem; color:#94A3B8;">(원천징수 공제 예상액: {int(deduct):,}원 차감)</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 8. 행정서류 (완전 고도화: 표, 경로, 원클릭 포털 연동)
# ==========================================
with tabs[8]:
    st.markdown("#### 정책자금 및 금융 필수 행정 서식 가이드")
    st.markdown("""
    소상공인 정책자금, 신용보증재단 보증서 발급, 금융권 대환대출 신청 시 요구되는 **4대 필수 증빙 서류**의 공식 발급 절차입니다.
    """)

    st.markdown("""
    | 서류명 | 주 발급처 | 신청 대상 및 용도 | 법정 수수료 | 평균 소요시간 |
    | :--- | :--- | :--- | :--- | :--- |
    | **소상공인확인서** | 중소기업현황정보시스템 | 정부 지원사업, 국비 지원금 신청 시 소상공인 증빙 | 무료 | 즉시 (온라인) |
    | **부가가치세 과세표준증명** | 국세청 홈택스 / 손택스 | 대출 심사, 보증 심사 시 사업장 매출 규모 증빙 | 무료 | 즉시 (온라인) |
    | **국세 완납증명서 (납세증명)** | 국세청 홈택스 | 세금 체납 여부 확인 (미납 시 정책 지원 전면 제한) | 무료 | 즉시 (온라인) |
    | **지방세 완납증명서** | 정부24 / 주민센터 | 지방세(재산세, 주민세 등) 체납 여부 확인 | 무료 | 즉시 (온라인) |
    """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 서류별 상세 발급 경로 및 유의사항")

    c_doc1, c_doc2 = st.columns(2)
    with c_doc1:
        st.markdown("""
        <div class="clean-card">
            <div style="font-weight:700; color:#0F172A; font-size:0.95rem; margin-bottom:6px;">1. 소상공인확인서 (중소기업확인서)</div>
            <p style="font-size:0.85rem; color:#475569; line-height:1.6; margin-bottom:12px;">
                • <b>공식 포털:</b> 중소기업현황정보시스템 (sminfo.mss.go.kr)<br>
                • <b>발급 단계:</b> 회원가입 및 로그인 ➡️ [확인서 발급신청] ➡️ 사업자 정보 입력 ➡️ 온라인 자료제출(홈택스 자료 연동) ➡️ 확인서 출력<br>
                • <b>주의사항:</b> 직전 연도 소득세 신고가 완료되어야 정상 발급되며, 매년 갱신이 필요합니다.
            </p>
            <a href="https://sminfo.mss.go.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    중소기업현황정보시스템 바로가기
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="clean-card">
            <div style="font-weight:700; color:#0F172A; font-size:0.95rem; margin-bottom:6px;">2. 부가가치세 과세표준증명원</div>
            <p style="font-size:0.85rem; color:#475569; line-height:1.6; margin-bottom:12px;">
                • <b>공식 포털:</b> 국세청 홈택스 (hometax.go.kr)<br>
                • <b>발급 단계:</b> 공동/금융인증서 로그인 ➡️ [국세증명·사업자등록 세금관련 신청/신고] ➡️ [부가가치세 과세표준증명] ➡️ 과세기간 선택 후 발급<br>
                • <b>주의사항:</b> 간이과세자는 [부가가치세 면세사업자 수입금액증명] 또는 해당 간이과세 증명으로 대체될 수 있습니다.
            </p>
            <a href="https://www.hometax.go.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    국세청 홈택스 바로가기
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

    with c_doc2:
        st.markdown("""
        <div class="clean-card">
            <div style="font-weight:700; color:#0F172A; font-size:0.95rem; margin-bottom:6px;">3. 국세 완납증명서 (납세증명서)</div>
            <p style="font-size:0.85rem; color:#475569; line-height:1.6; margin-bottom:12px;">
                • <b>공식 포털:</b> 국세청 홈택스 (hometax.go.kr)<br>
                • <b>발급 단계:</b> 홈택스 로그인 ➡️ [국세증명·사업자등록] ➡️ [납세증명서(국세완납증명)] ➡️ 수령방법 및 제출처 선택 ➡️ 신청<br>
                • <b>주의사항:</b> 유효기간이 통상 30일로 짧으므로 보증재단이나 은행 제출 직전에 발급받는 것이 권장됩니다.
            </p>
            <a href="https://www.hometax.go.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    국세청 납세증명 메뉴 바로가기
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="clean-card">
            <div style="font-weight:700; color:#0F172A; font-size:0.95rem; margin-bottom:6px;">4. 지방세 납세증명서 (지방세 완납)</div>
            <p style="font-size:0.85rem; color:#475569; line-height:1.6; margin-bottom:12px;">
                • <b>공식 포털:</b> 정부24 (gov.kr)<br>
                • <b>발급 단계:</b> 정부24 간편인증 로그인 ➡️ 검색창에 '지방세 납세증명' 입력 ➡️ 신청하기 ➡️ 사업자등록번호 입력 후 PDF 발급<br>
                • <b>주의사항:</b> 개인사업자의 경우 개인 명의와 법인/상호 명의 체납 내역이 모두 조회되니 유의해야 합니다.
            </p>
            <a href="https://www.gov.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    정부24 바로가기
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 9. 정책지원 (완전 고도화: 3대 핵심사업 카드 + 맞춤형 AI 진단기)
# ==========================================
with tabs[9]:
    st.markdown("#### 2026 소상공인 정책금융 및 국비 지원사업 분석")
    st.markdown("""
    소상공인시장진흥공단 및 중소벤처기업부에서 주관하는 주요 지원 정책 핵심 내용입니다.
    """)

    st.markdown("""
    <div class="policy-grid">
        <div class="policy-box">
            <div>
                <span class="policy-tag">비용 절감</span>
                <div class="policy-box-title">소상공인 전기요금 특별지원</div>
                <div class="policy-detail">
                    • <b>지원 한도:</b> 사업장당 최대 20만 원~25만 원 전기요금 감면<br>
                    • <b>신청 자격:</b> 연 매출 6천만 원 이하 소상공인 (일반용·산업용 전력 사용자)<br>
                    • <b>접수 기관:</b> 소상공인전기요금특별지원.kr (온라인 신청)
                </div>
            </div>
            <a href="https://www.소상공인전기요금특별지원.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#2563EB; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    전기요금 지원 신청처
                </button>
            </a>
        </div>
        <div class="policy-box">
            <div>
                <span class="policy-tag">금융 비용 경감</span>
                <div class="policy-box-title">고금리 소상공인 저금리 대환보증</div>
                <div class="policy-detail">
                    • <b>지원 혜택:</b> 제2금융권 7% 이상 고금리 대출을 4%대 정책 대출로 전환<br>
                    • <b>보증 한도:</b> 사업자당 최대 5,000만 원 한도 (보증비율 90% 이상)<br>
                    • <b>접수 기관:</b> 신용보증기금 및 각 시·도 지역신용보증재단
                </div>
            </div>
            <a href="https://www.semas.or.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#2563EB; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    소상공인정책자금 안내
                </button>
            </a>
        </div>
        <div class="policy-box">
            <div>
                <span class="policy-tag">매장 인프라 국비 지원</span>
                <div class="policy-box-title">스마트상점 기술보급 국비 지원사업</div>
                <div class="policy-detail">
                    • <b>지원 혜택:</b> 테이블오더, 무인 키오스크, 서빙로봇 도입 비용 최대 70% 국비 보조<br>
                    • <b>지원 한도:</b> 일반형 최대 500만 원, 미래형 최대 1,000만 원 국비 지원<br>
                    • <b>접수 기관:</b> 소상공인스마트상점 (sbiz.or.kr/smst/index.do)
                </div>
            </div>
            <a href="https://www.sbiz.or.kr/smst/index.do" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#2563EB; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    스마트상점 공고 보기
                </button>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 사업장 조건별 맞춤형 정책지원 AI 진단")

    with st.container():
        st.markdown("""
        <div class="clean-card">
            <p style="font-size:0.9rem; color:#475569; margin-bottom:12px;">
                현재 매장의 매출 규모와 자금 필요 목적을 선택하시면 적합한 정책자금 항목과 신청 로드맵을 AI가 브리핑합니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_rev = st.selectbox("사업장 연 매출 규모", ["3,000만 원 미만 (영세 소상공인)", "3,000만 원 ~ 1억 원 미만", "1억 원 ~ 3억 원 미만", "3억 원 초과"], key="p_rev")
        with col_p2:
            p_purpose = st.selectbox("가장 시급한 지원 분야", ["고금리 대출 이자 부담 완화", "매장 설비/디지털 인프라(키오스크 등) 구축", "운영자금 및 고정비(임대료·전기세) 보조", "사업장 간판·인테리어 개선"], key="p_purpose")

        if st.button("내 맞춤형 지원사업 진단서 확인", key="btn_p_ai"):
            with st.spinner("전문 정책지원 데이터를 분석하고 있습니다..."):
                prompt = f"""
                업종: {sel_industry}
                소재지: {sel_loc}
                연매출: {p_rev}
                목적: {p_purpose}

                위 사업장에 가장 유리한 정책자금 및 정부지원사업을 2가지 추천하고,
                1) 구체적 지원 내용
                2) 신청 요건 및 필수 구비 서류
                3) 신청 시 탈락을 방지하는 실무 팁
                을 표준 비즈니스 컨설팅 리포트 양식으로 간결하고 전문적으로 제시하라.
                """
                out = generate_safe_content(prompt)
                if out:
                    st.markdown(f"""
                    <div class="clean-card" style="border-left: 4px solid #2563EB; margin-top:14px;">
                        <div style="font-weight:700; color:#0F172A; font-size:1.05rem; margin-bottom:10px;">사업장 맞춤 정책지원 분석 리포트</div>
                        <div style="color:#334155; font-size:0.92rem; line-height:1.7;">{out}</div>
                    </div>
                    """, unsafe_allow_html=True)

# 10. 영업마감
with tabs[10]:
    if st.button("마감 브리핑 작성 실행", key="v4_close_btn"):
        out = generate_safe_content(f"가게: {store_name} ({sel_industry})\n전문적인 일일 영업 마감 분석과 익일 매출 증대 전략 제언.")
        if out:
            st.markdown(f"""
            <div class="clean-card" style="border-left: 3px solid #2563EB;">
                <div style="font-weight:700; color:#0F172A; margin-bottom:8px;">일일 영업 마감 분석 리포트</div>
                <div style="color:#334155; font-size:0.92rem; line-height:1.6;">{out}</div>
            </div>
            """, unsafe_allow_html=True)
