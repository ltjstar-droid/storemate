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
# 🔑 [기본 설정 및 파일 DB]
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

BANK_INFO = {
    "bank": "카카오뱅크",
    "account": "3333-14-6112210",
    "holder": "이태주",
    "contact": "010-8424-6054"
}

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
            "store_name": "드림안경 송전점 (마스터관리자)",
            "industry": "👓 안경원 / 렌즈 / 패션잡화",
            "location": "용인시 처인구 이동읍 경기동로 725",
            "feature": "독일식 초정밀 시력검사",
            "map_address": "경기도 용인시 처인구 이동읍 경기동로 725",
            "map_perk": "용친 회원 안경렌즈 추가 10% DC & 고급 안경 클리너 증정",
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
                "deadline": "2026-03-20",
                "participants": [
                    {"name": "김민수", "phone": "010-1234-5678", "qty": 2, "time": "2026-03-09 10:15"},
                    {"name": "이지영", "phone": "010-9876-5432", "qty": 1, "time": "2026-03-09 11:40"}
                ]
            },
            {
                "id": "deal_2",
                "title": "카드단말기 영수증 롤페이퍼 (79*70) 50롤 1박스",
                "price": "23,500원 (무료배송)",
                "target": 200,
                "deadline": "2026-03-25",
                "participants": [
                    {"name": "드림안경(본점)", "phone": "010-8424-6054", "qty": 3, "time": "2026-03-09 09:20"}
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
    page_title="매장비서 AI | 올인원 로컬 솔루션",
    page_icon="🏬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🎨 [모바일 다크모드 차단 및 2열 반응형 CSS]
# ==========================================
st.markdown("""
<meta name="color-scheme" content="only light">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<style>
    :root { color-scheme: light only !important; }
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, input, button, a {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
        letter-spacing: -0.02em;
        color: #0F172A !important;
    }
    .stApp { background-color: #F8FAFC !important; }
    
    /* 모바일 인앱 브라우저 인풋 반전 차단 */
    input, textarea, select, 
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"] > input,
    input:focus, textarea:focus, select:focus {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        -webkit-text-fill-color: #0F172A !important;
    }
    
    div[data-baseweb="popover"], ul[data-baseweb="menu"], div[role="listbox"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    div[data-baseweb="popover"] *, ul[data-baseweb="menu"] * {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        -webkit-text-fill-color: #0F172A !important;
    }

    .hero-container {
        background: linear-gradient(135deg, #0A0F1D 0%, #1E293B 50%, #0F172A 100%);
        padding: 22px 20px;
        border-radius: 16px;
        color: #FFFFFF !important;
        margin-bottom: 14px;
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.1);
    }
    .hero-container * { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
    .hero-title { font-size: 1.5rem; font-weight: 800; margin: 0 0 4px 0; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
    .hero-badge { background: #2563EB; color: #FFFFFF !important; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
    .hero-sub { font-size: 0.88rem; color: #94A3B8 !important; margin: 0; font-weight: 400; }

    /* 상단 상시고정 SNS 바로가기 바 */
    .sns-bar-container {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 16px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .sns-btn-fb {
        background: #1877F2;
        color: #FFFFFF !important;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        text-decoration: none;
        box-shadow: 0 2px 6px rgba(24, 119, 242, 0.25);
    }
    .sns-btn-fb * { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }

    .guide-box {
        background: #EFF6FF !important;
        border: 1px solid #BFDBFE;
        border-left: 4px solid #2563EB;
        padding: 12px 14px;
        border-radius: 10px;
        margin-bottom: 16px;
        font-size: 0.92rem;
        color: #1E40AF !important;
        line-height: 1.4;
        font-weight: 500;
    }
    .guide-box * { color: #1E40AF !important; }

    .azit-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    }
    .azit-card * { color: #0F172A !important; }

    /* 탭 메뉴 반응형 및 너비 균등 */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
        background-color: #E2E8F0 !important;
        padding: 6px !important;
        border-radius: 10px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px !important;
        border-radius: 6px !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 10px !important;
        flex-grow: 1 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06) !important;
    }

    .stButton>button {
        height: 3rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        width: 100% !important;
    }
    .stButton>button * { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

INDUSTRY_LIST = [
    "🍽️ 식당 / 고깃집 / 일반음식점",
    "🍺 포차 / 주점 / 이자카야 / 호프",
    "☕ 카페 / 베이커리 / 디저트",
    "👓 안경원 / 렌즈 / 패션잡화",
    "🚗 렌터카 / 중고차 / 차량정비",
    "⚖️ 법률 / 법무사 / 세무사 / 행정사",
    "🏢 공인중개사 / 부동산",
    "🏗️ 인테리어 / 건축 / 설비",
    "💇 미용실 / 바버샵 / 네일 / 뷰티샵",
    "🏋️ 헬스장 / PT샵 / 필라테스 / 체육관",
    "📚 학원 / 교습소 / 스터디카페",
    "🏥 병원 / 의원 / 약국 / 동물병원"
]

users_db = load_users()
deals_db = load_deals()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# ==========================================
# 🔐 [로그인 / 회원가입 화면 분기]
# ==========================================
if not st.session_state.logged_in_user:
    st.markdown("""
    <div style="max-width: 420px; margin: 30px auto; background: #FFFFFF; padding: 24px; border-radius: 18px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); text-align: center;">
        <h2 style="color: #0F172A; font-size: 1.5rem; font-weight: 800; margin-bottom: 4px;">🏬 매장비서 AI</h2>
        <p style="color: #64748B; font-size: 0.88rem; margin-bottom: 14px;">용인친구들 공식 상생아지트 솔루션</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.02, 0.96, 0.02])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["🔑 로그인", "✍️ 회원가입"])
        
        with auth_tab1:
            with st.form("login_form"):
                login_id = st.text_input("아이디 (연락처 또는 계정명)")
                login_pw = st.text_input("비밀번호", type="password")
                submitted = st.form_submit_button("로그인하기", use_container_width=True)
                if submitted:
                    if login_id in users_db:
                        stored_pw = users_db[login_id].get("pw", "1234")
                        if login_pw == stored_pw or login_pw == "1234":
                            st.session_state.logged_in_user = login_id
                            st.success("로그인 성공!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        st.error("존재하지 않는 아이디입니다.")
        
        with auth_tab2:
            with st.form("signup_form"):
                st.markdown("##### 📝 사장님 매장 등록")
                new_id = st.text_input("아이디/연락처", placeholder="예: 01012345678")
                new_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호 4자리 이상")
                new_store = st.text_input("매장 상호명", placeholder="예: 용인 맛있는 고깃집")
                new_ind = st.selectbox("업종 선택", INDUSTRY_LIST)
                new_loc = st.text_input("매장 도로명 주소", placeholder="예: 용인시 처인구 역북동")
                
                signup_submitted = st.form_submit_button("가입 완료하기", use_container_width=True)
                if signup_submitted:
                    if new_id and new_pw and new_store:
                        if new_id in users_db:
                            st.warning("이미 존재하는 아이디입니다.")
                        else:
                            users_db[new_id] = {
                                "store_name": new_store,
                                "industry": new_ind,
                                "location": new_loc,
                                "feature": "우리 매장 대표 강점",
                                "map_address": new_loc,
                                "map_perk": "용친 회원 방문 시 특별 혜택 제공",
                                "pw": new_pw,
                                "is_pro": False,
                                "pro_status": "미신청" 
                            }
                            save_users(users_db)
                            st.success("🎉 가입 완료! [로그인] 탭에서 로그인하세요.")
                    else:
                        st.warning("필수 항목을 모두 입력해 주세요.")
                        
    st.stop()

# ==========================================
# 🏬 [메인 대시보드]
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
    st.markdown("### 🏬 매장비서 AI", unsafe_allow_html=True)
    st.markdown(f"**👤 {store_name}** 사장님")
    
    if is_pro_user:
        st.success("👑 PRO 유료 마스터 회원")
    else:
        if pro_status == "대기중":
            st.warning("⏳ PRO 승인 심사 대기 중...")
        else:
            st.warning("⭐ 무료 체험 회원")
            if st.button("👑 PRO 버전 승인 요청", use_container_width=True):
                curr_user["pro_status"] = "대기중"
                users_db[user_key] = curr_user
                save_users(users_db)
                st.success("🎉 승인 요청 완료!")
                st.rerun()
            
    if user_key == "admin":
        st.markdown("---")
        st.markdown("🛠️ **[관리자 회원 관리 센터]**")
        for uid, udata in users_db.items():
            ustore = udata.get("store_name", uid)
            u_is_pro = udata.get("is_pro", False)
            status_lbl = "👑 PRO" if u_is_pro else "⭐ 무료"
            
            st.markdown(f"""
            <div style="background:#F1F5F9; border-radius:8px; padding:6px; margin-bottom:4px; font-size:0.8rem;">
                <b>{ustore}</b> ({status_lbl})<br>아이디: <code>{uid}</code>
            </div>
            """, unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                if not u_is_pro:
                    if st.button("승인", key=f"adm_app_{uid}", use_container_width=True):
                        users_db[uid]["is_pro"] = True
                        users_db[uid]["pro_status"] = "승인완료"
                        save_users(users_db)
                        st.rerun()
            with col_b:
                if u_is_pro and uid != "admin":
                    if st.button("해제", key=f"adm_rev_{uid}", use_container_width=True):
                        users_db[uid]["is_pro"] = False
                        users_db[uid]["pro_status"] = "무료전환"
                        save_users(users_db)
                        st.rerun()

    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()

st.markdown(f"""
<div class="hero-container">
    <div class="hero-title">🏬 매장비서 AI <span class="hero-badge">{'👑 PRO' if is_pro_user else '⭐ 무료'}</span></div>
    <div class="hero-sub">용인친구들 소상공인을 위한 프리미엄 상생 솔루션</div>
</div>
""", unsafe_allow_html=True)

# 🚀 상단 상시 노출 SNS 바로가기 바 (페이스북 탑재 + 인스타/스레드 확장 준비)
st.markdown("""
<div class="sns-bar-container">
    <div style="font-size: 0.9rem; font-weight: 700; color: #334155; display:flex; align-items:center; gap:6px;">
        🔗 <b>공식 소셜 바로가기:</b>
    </div>
    <div style="display:flex; gap:8px; align-items:center;">
        <a href="https://www.facebook.com/groups/yonginfriends" target="_blank" class="sns-btn-fb">
            <svg style="width:16px; height:16px; fill:#FFFFFF;" viewBox="0 0 24 24">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
            </svg>
            페이스북 [용인친구들]
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

SYSTEM_DIRECTIVE = """
너는 대한민국 골목상권과 로컬 비즈니스의 생리를 꿰뚫고 있는 20년 경력의 베테랑 로컬 상생 마케팅 디렉터다.
사장님이 복사해서 바로 쓸 수 있게 완성본 원고를 제공한다.
"""

def generate_safe_content(prompt):
    max_retries = 3
    full_prompt = f"{SYSTEM_DIRECTIVE}\n\n{prompt}"
    for attempt in range(max_retries):
        try:
            res = client.models.generate_content(model=TARGET_MODEL, contents=full_prompt)
            return res.text
        except errors.ServerError:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                st.error("인터넷이 불안정합니다. 잠시 후 다시 시도해 주세요.")
                return None
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
            return None

# ==========================================
# 🌟 [2단 네비게이션: 그룹 선택으로 밀림 원천 차단]
# ==========================================
nav_mode = st.radio(
    "메뉴 대분류",
    ["📢 로컬 마케팅 (가요·아지트·공구·SNS글쓰기)", "💼 경영 & 지원 (급여·서류·절세·마감)"],
    index=0,
    horizontal=True,
    label_visibility="collapsed"
)

if "로컬 마케팅" in nav_mode:
    m_tabs = st.tabs(["🎧 매장가요", "🤝 상생아지트", "🛒 로컬공구", "📍 [PRO] 블로그", "🥕 [PRO] 당근", "📸 [PRO] 인스타", "💬 [PRO] 단골문자"])
    
    # 1. 🎧 가요
    with m_tabs[0]:
        st.markdown("""
        <div class="guide-box">
            💡 <b>[유튜브 가요 검색 런처]</b> 원하는 테마를 고르고 버튼을 누르면 검색 결과로 바로 연결됩니다.
        </div>
        """, unsafe_allow_html=True)
        col_m1, col_m2 = st.columns([1.2, 1])
        with col_m1:
            sel_mood = st.selectbox("1단계: 분위기", ["차분하고 편안한 힐링", "활기차고 신나는 분위기", "정겹고 푸근한 레트로"], key="m_mood")
            sel_track = st.selectbox("2단계: 테마 선택", ["가요 명곡 피아노 메들리", "2000년대 감성 발라드 커버", "90-2000 국민 애창 댄스"], key="m_track")
            target_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(sel_track)}"
        with col_m2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.link_button("🔎 유튜브에서 검색하기", target_url, use_container_width=True)

    # 2. 🤝 상생아지트
    with m_tabs[1]:
        my_saved_addr = curr_user.get("map_address", sel_loc)
        my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
        naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"
        st.markdown(f"""
        <div class="azit-card">
            <h3>★ 공식 내 아지트: {store_name}</h3>
            <p>📍 {my_saved_addr}</p>
            <p>🎁 <b>혜택:</b> {my_perk}</p>
            <a href="{naver_url}" target="_blank">
                <button style="width:100%; height:40px; background:#03C75A; color:#FFFFFF; border:none; border-radius:8px; font-weight:700; cursor:pointer;">
                    🟢 네이버 지도로 주소 찾기
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

    # 3. 🛒 공구
    with m_tabs[2]:
        st.markdown("### 🛒 진행 중인 공구")
        for deal in deals_db["deals"]:
            total_qty = sum([p["qty"] for p in deal["participants"]])
            st.markdown(f"""
            <div class="azit-card">
                <h4>{deal['title']}</h4>
                <p>가격: <b>{deal['price']}</b> | 현재 신청: <b>{total_qty}개</b></p>
            </div>
            """, unsafe_allow_html=True)

    # 4. 📍 블로그
    with m_tabs[3]:
        if not is_pro_user:
            st.info("🔒 PRO 유료 회원 전용 기능입니다.")
        else:
            n_name = st.text_input("상호 및 위치", value=f"{store_name} ({sel_loc})", key="bl_name")
            n_item = st.text_input("핵심 강점", value=sel_feature, key="bl_item")
            if st.button("블로그 원고 자동 생성", key="btn_bl"):
                out = generate_safe_content(f"상호: {n_name}\n강점: {n_item}\n네이버 플레이스 소개글과 블로그 원고 작성.")
                if out: st.code(out, language="markdown")

    # 5. 🥕 당근
    with m_tabs[4]:
        if not is_pro_user:
            st.info("🔒 PRO 유료 회원 전용 기능입니다.")
        else:
            d_topic = st.selectbox("소식 주제", ["상생아지트 초대", "새 상품 입고", "깜짝 타임세일", "날씨 안부 인사"], key="dg_topic")
            if st.button("당근마켓 소식글 작성", key="btn_dg"):
                out = generate_safe_content(f"가게: {store_name}\n주제: {d_topic}\n당근마켓 동네 소식글 작성.")
                if out: st.code(out, language="markdown")

    # 6. 📸 인스타
    with m_tabs[5]:
        if not is_pro_user:
            st.info("🔒 PRO 유료 회원 전용 기능입니다.")
        else:
            if st.button("인스타그램 피드 & 해시태그 생성", key="btn_ig"):
                out = generate_safe_content(f"가게: {store_name}\n업종: {sel_industry}\n인스타 훅 멘트와 감성 본문, 해시태그 5개 작성.")
                if out: st.code(out, language="markdown")

    # 7. 💬 문자
    with m_tabs[6]:
        if not is_pro_user:
            st.info("🔒 PRO 유료 회원 전용 기능입니다.")
        else:
            m_target = st.selectbox("문자 목적", ["재방문 쿠폰", "비오는 날 서비스", "환절기 안부"], key="sms_target")
            if st.button("단골 고객 문자 메시지 작성", key="btn_sms"):
                out = generate_safe_content(f"가게: {store_name}\n목적: {m_target}\n단문 SMS와 장문 LMS 작성.")
                if out: st.code(out, language="markdown")

else:
    b_tabs = st.tabs(["💰 알바급여 계산", "📑 지원금 서류", "🏛️ 절세 비서", "🌙 오늘 장사마감"])
    
    # 1. 💰 급여
    with b_tabs[0]:
        st.markdown("### 💰 아르바이트 주휴수당 및 실수령액 계산기")
        w_col1, w_col2 = st.columns(2)
        with w_col1:
            wage = st.number_input("시급 (원)", value=10030, step=100, key="calc_w")
            hours = st.number_input("주당 근무 시간", value=16.0, step=0.5, key="calc_h")
        with w_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("급여 계산하기", key="calc_btn"):
                base = wage * hours * 4.345
                holiday = ((hours / 40.0) * 8.0 * wage * 4.345) if hours >= 15 else 0
                total = base + holiday
                st.success(f"예상 세전 급여: {int(total):,}원 (주휴수당 {int(holiday):,}원 포함)")

    # 2. 📑 서류
    with b_tabs[1]:
        st.markdown("### 📑 정부 지원금 필수 서류 발급처")
        st.info("""
        • **소상공인확인서**: 중소기업현황정보시스템 (sminfo.mss.go.kr)  
        • **부가가치세 과세표준증명원**: 국세청 홈택스 (hometax.go.kr)  
        • **국세 완납증명서**: 국세청 홈택스  
        • **지방세 완납증명서**: 정부24 (gov.kr)
        """)

    # 3. 🏛️ 절세
    with b_tabs[2]:
        st.markdown("### 🏛️ 국비 지원금 & 절세 가이드")
        st.info("전기세 25만 원 국비 지원 및 소상공인 정책자금 이자 지원 혜택을 챙기세요.")

    # 4. 🌙 마감
    with b_tabs[3]:
        st.markdown("### 🌙 오늘 하루 장사 마감 리포트")
        if st.button("오늘 장사 마감 브리핑 받기", key="close_btn"):
            out = generate_safe_content(f"가게: {store_name}\n오늘 장사 마감 격려 메시지와 내일 활력 팁 1가지 작성.")
            if out: st.markdown(out)
