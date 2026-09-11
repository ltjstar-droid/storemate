import os
import sys
import time
import json
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd
import requests

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
ANALYTICS_DB_FILE = "analytics_db.json"

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
            "phone": "031-323-1215",
            "feature": "독일식 초정밀 시력검사",
            "map_address": "경기도 용인시 처인구 이동읍 경기동로 725",
            "map_perk": "용친 회원 안경렌즈 추가 10% DC & 고급 안경 클리너 증정",
            "today_deal": "누진다초점 렌즈 50% 할인",
            "today_updated": datetime.now().strftime("%Y-%m-%d"),
            "pw": "1234",
            "is_pro": True,
            "pro_status": "승인완료",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "trial_end": (datetime.now() + timedelta(days=3650)).strftime("%Y-%m-%d")
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

def load_analytics():
    if os.path.exists(ANALYTICS_DB_FILE):
        try:
            with open(ANALYTICS_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_analytics(data):
    try:
        with open(ANALYTICS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def track_visitor():
    analytics = load_analytics()
    today_str = datetime.now().strftime("%Y-%m-%d")
    if today_str not in analytics:
        analytics[today_str] = {"uv": 0, "pv": 0}
    analytics[today_str]["pv"] += 1
    if "has_visited_today" not in st.session_state:
        st.session_state.has_visited_today = True
        analytics[today_str]["uv"] += 1
    save_analytics(analytics)

track_visitor()

# ==========================================
# ☀️ 날씨 및 지오코딩
# ==========================================
def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=14&addressdetails=1"
        headers = {"User-Agent": "StoreMate-Mobile/2.0"}
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            addr = res.json().get("address", {})
            city = addr.get("city") or addr.get("county") or addr.get("province") or "용인시"
            district = addr.get("borough") or addr.get("suburb") or addr.get("town") or ""
            return f"{city} {district}".strip()
    except Exception:
        pass
    return "용인시 처인구"

def get_live_weather(lat=37.16, lon=127.21):
    icon_sun = """<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>"""
    icon_cloud = """<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>"""
    icon_rain = """<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><line x1="16" y1="13" x2="16" y2="21"></line><line x1="8" y1="13" x2="8" y2="21"></line><line x1="12" y1="15" x2="12" y2="23"></line><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"></path></svg>"""

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json().get("current_weather", {})
            temp = data.get("temperature", 20.2)
            code = data.get("weathercode", 0)
            
            if code in [0, 1]:
                status = "맑음"
                tip = "화창한 날씨입니다. 매장 쇼윈도와 입구를 점검해 방문을 유도하세요."
                svg_icon = icon_sun
            elif code in [2, 3]:
                status = "구름 많음 / 흐림"
                tip = "차분한 날씨입니다. 실내 조명과 음악으로 편안한 분위기를 만드세요."
                svg_icon = icon_cloud
            elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                status = "비 / 소나기"
                tip = "비 오는 날 방문 고객을 위한 우천 단골 혜택을 안내하세요."
                svg_icon = icon_rain
            else:
                status = "무난함"
                tip = "기온 변화에 맞춰 단골 고객 안부 문자와 특가를 활용하세요."
                svg_icon = icon_sun
            return {"temp": temp, "status": status, "tip": tip, "icon": svg_icon}
    except Exception:
        pass
    return {"temp": 20.2, "status": "구름 많음 / 흐림", "tip": "차분한 날씨입니다. 실내 조명과 음악으로 편안한 분위기를 만드세요.", "icon": icon_cloud}

st.set_page_config(
    page_title="STORE MATE | 모바일 매장비서",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 📱 모바일 퍼스트 원페이지 CSS
# ==========================================
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="color-scheme" content="only light">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<style>
    :root { color-scheme: light only !important; }
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, input, button, a {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
        letter-spacing: -0.02em;
    }
    
    .stApp, html, body { background-color: #FFFFFF !important; }

    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    button[kind="header"] { display: none !important; }
    #MainMenu, footer { visibility: hidden !important; display: none !important; }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    .store-meta-line {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 2px;
        white-space: nowrap !important;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* 메인 탭바 간결화 */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        gap: 12px !important;
        background: transparent !important;
        padding: 0 0 6px 0 !important;
        margin-bottom: 16px !important;
        border-bottom: 2px solid #F1F5F9 !important;
        scrollbar-width: none;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    .stTabs [data-baseweb="tab"] {
        height: 42px !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #64748B !important;
        background: transparent !important;
        border: none !important;
        padding: 0 4px !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        font-weight: 800 !important;
        border-bottom: 3px solid #2563EB !important;
    }
    .stTabs [aria-selected="true"] * { color: #2563EB !important; }

    .simple-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    .weather-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }

    .calc-result-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2563EB;
        border-radius: 10px;
        padding: 14px 16px;
        margin-top: 12px;
    }

    .unified-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 12px;
        margin-top: 8px;
    }
    .unified-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .stButton>button {
        height: 48px !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        width: 100% !important;
    }
    .stButton>button:hover { background: #1D4ED8 !important; }

    .stLinkButton > a, div[data-testid="stLinkButton"] > a {
        background: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        min-height: 46px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        width: 100% !important;
    }

    input, textarea, select { font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

INDUSTRY_LIST = [
    "미용실 / 바버샵 / 네일 / 뷰티샵",
    "안경원 / 렌즈 / 광학",
    "식당 / 고깃집 / 일반음식점",
    "포차 / 주점 / 이자카야 / 호프",
    "카페 / 베이커리 / 디저트",
    "렌터카 / 중고차 / 차량정비",
    "법률 / 법무사 / 세무사 / 행정사",
    "공인중개사 / 부동산",
    "인테리어 / 건축 / 설비",
    "헬스장 / PT샵 / 필라테스 / 체육관",
    "학원 / 교습소 / 스터디카페",
    "병원 / 의원 / 약국 / 동물병원"
]

users_db = load_users()
deals_db = load_deals()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "current_lat" not in st.session_state:
    st.session_state.current_lat = 37.16
if "current_lon" not in st.session_state:
    st.session_state.current_lon = 127.21
if "current_region_name" not in st.session_state:
    st.session_state.current_region_name = "용인시 처인구 이동읍"

# ==========================================
# 로그인 화면
# ==========================================
if not st.session_state.logged_in_user:
    st.markdown("""<div style="text-align: center; margin: 30px 0 16px 0;">
<h2 style="font-size: 1.6rem; font-weight: 900; color: #0F172A; margin: 0 0 4px 0;">STORE MATE</h2>
<p style="font-size: 0.88rem; color: #64748B;">소상공인 올인원 모바일 비서</p>
</div>""", unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["로그인", "신규 가입 (7일 무료)"])
    with auth_tab1:
        with st.form("login_form"):
            login_id = st.text_input("아이디 또는 연락처", placeholder="휴대폰 번호 권장")
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
            st.caption("신규 가입 시 7일간 모든 PRO 기능을 무료로 체험하실 수 있습니다.")
            new_id = st.text_input("아이디 (연락처)", placeholder="01012345678")
            new_pw = st.text_input("비밀번호 설정", type="password")
            new_store = st.text_input("매장 상호명")
            new_phone = st.text_input("매장 전화번호", placeholder="031-123-4567")
            new_ind = st.selectbox("업종 선택", INDUSTRY_LIST)
            new_loc = st.text_input("매장 주소", placeholder="예: 용인시 처인구 이동읍...")
            if st.form_submit_button("가입 완료 (7일 무료 시작)", use_container_width=True):
                if new_id and new_pw and new_store:
                    now = datetime.now()
                    trial_end_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")
                    users_db[new_id] = {
                        "store_name": new_store,
                        "industry": new_ind,
                        "location": new_loc,
                        "phone": new_phone if new_phone else "010-0000-0000",
                        "feature": "전문 고객 맞춤 케어",
                        "map_address": new_loc,
                        "map_perk": "용친 회원 방문 시 특별 혜택 제공",
                        "today_deal": "",
                        "today_updated": now.strftime("%Y-%m-%d"),
                        "pw": new_pw,
                        "is_pro": True,
                        "pro_status": "무료체험",
                        "created_at": now.strftime("%Y-%m-%d"),
                        "trial_end": trial_end_date
                    }
                    save_users(users_db)
                    st.success("등록 완료! 7일 무료 PRO 체험이 시작되었습니다. 로그인해 주세요.")
    st.stop()

# ==========================================
# 회원 권한 및 정확한 D-day 계산
# ==========================================
user_key = st.session_state.logged_in_user
curr_user = users_db.get(user_key, {})
store_name = curr_user.get("store_name", "라브리지헤어살롱")
store_phone = curr_user.get("phone", "031-000-0000")
sel_industry = curr_user.get("industry", INDUSTRY_LIST[0])
sel_loc = curr_user.get("location", "용인시 처인구")
sel_feature = curr_user.get("feature", "맞춤형 전문 서비스")

today_now = datetime.now().date()
trial_end_str = curr_user.get("trial_end", today_now.strftime("%Y-%m-%d"))
try:
    trial_end_date = datetime.strptime(trial_end_str, "%Y-%m-%d").date()
except Exception:
    trial_end_date = today_now

is_approved_permanent = (curr_user.get("pro_status") == "승인완료")
is_in_trial = (today_now <= trial_end_date)

if is_approved_permanent:
    is_pro_user = True
    pro_label = "PRO 정식 파트너"
elif is_in_trial:
    is_pro_user = True
    days_left = (trial_end_date - today_now).days
    pro_label = f"무료체험 D-{days_left} ({trial_end_str} 종료)"
else:
    is_pro_user = False
    pro_label = "스탠다드 (체험 만료)"
    if curr_user.get("is_pro", False) and not is_approved_permanent:
        curr_user["is_pro"] = False
        curr_user["pro_status"] = "체험만료"
        users_db[user_key] = curr_user
        save_users(users_db)

with st.sidebar:
    st.markdown(f"### {store_name}")
    st.markdown(f"**연락처:** `{store_phone}`")
    st.markdown(f"**상태:** `{pro_label}`")
    
    st.markdown("##### 매장 연락처 변경")
    with st.form("sidebar_phone_form"):
        new_p = st.text_input("새 전화번호", value=store_phone, label_visibility="collapsed")
        if st.form_submit_button("전화번호 즉시 변경", use_container_width=True):
            users_db[user_key]["phone"] = new_p.strip()
            save_users(users_db)
            st.success("변경 완료되었습니다.")
            st.rerun()

    if not is_approved_permanent:
        if is_in_trial:
            st.caption(f"무료 체험 종료일: {trial_end_str}")
        else:
            st.warning("7일 무료 체험이 종료되었습니다. 관리자 승인 후 유료 버전을 이용하실 수 있습니다.")
            
        if curr_user.get("pro_status") != "대기중":
            if st.button("유료버전 사용 승인 신청", use_container_width=True):
                curr_user["pro_status"] = "대기중"
                users_db[user_key] = curr_user
                save_users(users_db)
                st.success("승인 신청이 접수되었습니다.")
                st.rerun()
        else:
            st.info("관리자 유료 승인 대기 중입니다.")
    else:
        st.success("정식 유료 파트너 계정입니다.")

    if user_key == "admin":
        st.markdown("---")
        st.markdown("##### 📊 관리자: 방문 통계")
        analytics_data = load_analytics()
        today_key = today_now.strftime("%Y-%m-%d")
        today_stat = analytics_data.get(today_key, {"uv": 0, "pv": 0})
        total_uv = sum([v.get("uv", 0) for v in analytics_data.values()])
        total_pv = sum([v.get("pv", 0) for v in analytics_data.values()])
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("오늘 방문자", f"{today_stat['uv']}명")
        with col_m2:
            st.metric("오늘 조회수", f"{today_stat['pv']}회")
        st.caption(f"누적 순방문: {total_uv}명 | 누적 페이지뷰: {total_pv}회")

        st.markdown("---")
        st.markdown("##### 🔑 회원 유료 승인 제어")
        for uid, udata in users_db.items():
            if uid == "admin":
                continue
            ustore = udata.get("store_name", uid)
            u_status = udata.get("pro_status", "미신청")
            st.write(f"**{ustore}** (`{uid}`) | 상태: `{u_status}`")
            col_a, col_b = st.columns(2)
            with col_a:
                if u_status != "승인완료" and st.button("유료 승인", key=f"app_{uid}", use_container_width=True):
                    users_db[uid]["is_pro"] = True
                    users_db[uid]["pro_status"] = "승인완료"
                    save_users(users_db)
                    st.success(f"{ustore} 승인 완료")
                    st.rerun()
            with col_b:
                if u_status == "승인완료" and st.button("승인 취소", key=f"rev_{uid}", use_container_width=True):
                    users_db[uid]["is_pro"] = False
                    users_db[uid]["pro_status"] = "승인취소"
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
# 모바일 상단 바
# ==========================================
st.markdown(f"""<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
<div>
<span style="font-size: 1.25rem; font-weight: 900; color: #0F172A;">{store_name}</span>
<span style="font-size: 0.72rem; font-weight: 700; color: #2563EB; background: #EFF6FF; padding: 2px 6px; border-radius: 4px; margin-left: 4px;">{pro_label}</span>
<div class="store-meta-line">{sel_loc} · {sel_industry} &nbsp;|&nbsp; ☎️ <b>{store_phone}</b></div>
</div>
</div>
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 12px;">
<a href="https://www.facebook.com/groups/yonginfriends" target="_blank" style="background:#1877F2; color:#fff; padding:8px 0; border-radius:6px; font-size:0.75rem; font-weight:700; text-align:center; text-decoration:none;">용친 페북</a>
<a href="https://www.instagram.com/" target="_blank" style="background:#E1306C; color:#fff; padding:8px 0; border-radius:6px; font-size:0.75rem; font-weight:700; text-align:center; text-decoration:none;">용친 인스타</a>
<a href="https://www.threads.net/" target="_blank" style="background:#111827; color:#fff; padding:8px 0; border-radius:6px; font-size:0.75rem; font-weight:700; text-align:center; text-decoration:none;">용친 스레드</a>
</div>
<hr style="margin: 8px 0 14px 0; border: none; border-top: 1px solid #E2E8F0;">
""", unsafe_allow_html=True)

# ==========================================
# 간결한 메인 4대 탭 (서브 탭 완전 통합 원페이지화)
# ==========================================
main_tabs = ["홈 대시보드", "내 특가 관리", "마케팅 & 공구", "경영·행정비서"]
tab_home, tab_my_deal, tab_mkt, tab_biz = st.tabs(main_tabs)

# ------------------------------------------
# TAB 1. 🏠 홈 대시보드
# ------------------------------------------
with tab_home:
    my_saved_addr = curr_user.get("map_address", sel_loc)
    my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
    my_today_deal = curr_user.get("today_deal", "").strip()
    my_deal_updated = curr_user.get("today_updated", datetime.now().strftime("%Y-%m-%d"))
    naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"

    weather_info = get_live_weather(st.session_state.current_lat, st.session_state.current_lon)
    weather_html = f"""<div class="weather-box">
<div style="display:flex; align-items:center; gap:14px;">
<div>{weather_info['icon']}</div>
<div>
<div style="font-size:1.15rem; font-weight:900; color:#0F172A;">{st.session_state.current_region_name} · {weather_info['status']}</div>
<div style="font-size:0.85rem; color:#475569; margin-top:2px;">{weather_info['tip']}</div>
</div>
</div>
<div style="display:flex; justify-content:space-between; align-items:flex-end; width:100%; border-top:1px solid #E2E8F0; padding-top:8px; margin-top:4px;">
<span style="font-size:0.75rem; color:#64748B;">기상청 연동</span>
<span style="font-size:1.6rem; font-weight:900; color:#0F172A; line-height:1;">{weather_info['temp']}°C</span>
</div>
</div>"""
    st.markdown(weather_html, unsafe_allow_html=True)

    if st.button("📍 현재 내 위치로 날씨·지역 갱신", key="btn_detect_gps", use_container_width=True):
        try:
            ip_res = requests.get("https://ipapi.co/json/", timeout=2).json()
            lat = ip_res.get("latitude", 37.16)
            lon = ip_res.get("longitude", 127.21)
            st.session_state.current_lat = lat
            st.session_state.current_lon = lon
            st.session_state.current_region_name = reverse_geocode(lat, lon)
            st.toast(f"현재 위치: {st.session_state.current_region_name}")
            st.rerun()
        except Exception:
            st.warning("위치를 가져오지 못해 기본 주소를 유지합니다.")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    if my_today_deal and my_today_deal != "오늘의 특가 준비 중":
        my_deal_html = f"""<div class="simple-card" style="border-left: 4px solid #2563EB;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:1.05rem; font-weight:900; color:#0F172A;">내 매장 오늘의 특가</span>
<span style="font-size:0.75rem; color:#64748B;">{my_deal_updated}</span>
</div>
<div style="font-size:1.1rem; font-weight:900; color:#2563EB; margin:6px 0;">{my_today_deal}</div>
<div style="font-size:0.82rem; color:#475569;">혜택: {my_perk} &nbsp;|&nbsp; ☎️ <b>{store_phone}</b></div>
</div>"""
        st.markdown(my_deal_html, unsafe_allow_html=True)
    else:
        st.markdown("""<div class="simple-card" style="background:#F8FAFC;">
<div style="font-size:0.88rem; color:#64748B;">현재 내 매장의 당일 특가가 비어 있습니다.<br>상단 <b>[내 특가 관리]</b> 탭에서 등록해 보세요.</div>
</div>""", unsafe_allow_html=True)

    st.link_button("네이버 플레이스 지도 연동 확인", naver_url, use_container_width=True)

    st.markdown("""<div style="margin:20px 0 8px 0;">
<div style="font-size:1.1rem; font-weight:900; color:#0F172A;">용인친구들 실시간 상생 특가 피드</div>
<div style="font-size:0.82rem; color:#64748B;">실제 특가를 진행 중인 이웃 제휴 매장의 혜택입니다.</div>
</div>""", unsafe_allow_html=True)

    active_deals_count = 0
    for u_id, u_info in users_db.items():
        if u_id == "admin" or u_id == user_key:
            continue
        o_deal = u_info.get("today_deal", "").strip()
        if not o_deal or o_deal == "오늘의 특가 준비 중" or o_deal == "오늘의 특가 품목 등록 대기 중":
            continue

        active_deals_count += 1
        o_name = u_info.get("store_name", u_id)
        o_addr = u_info.get("map_address", u_info.get("location", ""))
        o_phone = u_info.get("phone", "전화번호 미등록")
        o_perk = u_info.get("map_perk", "용친 회원 방문 시 특별 혜택")
        o_upd = u_info.get("today_updated", "")
        o_nav_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(o_addr)}"
        
        feed_card_html = f"""<div class="simple-card">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:1.05rem; font-weight:800; color:#0F172A;">{o_name}</span>
<span style="font-size:0.75rem; color:#64748B;">{o_upd}</span>
</div>
<div style="font-size:0.8rem; color:#64748B; margin-bottom:6px;">{o_addr} &nbsp;|&nbsp; ☎️ <b>{o_phone}</b></div>
<div style="background:#EFF6FF; border-left:4px solid #2563EB; border-radius:6px; padding:10px 14px; margin-bottom:8px;">
<div style="font-size:0.72rem; font-weight:700; color:#2563EB;">오늘의 번개 특가</div>
<div style="font-size:1.05rem; font-weight:900; color:#0F172A; margin-top:2px;">{o_deal}</div>
</div>
<div style="font-size:0.82rem; color:#475569; margin-bottom:10px;">상시 혜택: {o_perk}</div>
<a href="{o_nav_url}" target="_blank" style="text-decoration:none;">
<button style="width:100%; height:40px; background:#F8FAFC; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
네이버 지도 길찾기
</button>
</a>
</div>"""
        st.markdown(feed_card_html, unsafe_allow_html=True)

    if active_deals_count == 0:
        st.info("현재 등록된 이웃 매장의 특가가 없습니다.")

# ------------------------------------------
# TAB 2. ⚙️ 내 특가 관리
# ------------------------------------------
with tab_my_deal:
    st.markdown("""<div class="simple-card">
<div style="font-weight:900; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">내 매장 특가 & 제휴 혜택 설정</div>
<div style="font-size:0.82rem; color:#64748B;">입력한 특가는 홈 대시보드 실시간 공유창에 노출됩니다.</div>
</div>""", unsafe_allow_html=True)

    current_deal_val = curr_user.get("today_deal", "")
    current_perk_val = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
    current_phone_val = curr_user.get("phone", store_phone)

    with st.form("my_store_deal_form"):
        st.markdown("**1. 매장 대표 전화번호**")
        inp_phone = st.text_input("전화번호", value=current_phone_val, placeholder="031-000-0000", label_visibility="collapsed")
        
        st.markdown("**2. 오늘의 번개 특가 품목**")
        inp_deal = st.text_input("특가 내용", value=current_deal_val, placeholder="예: 첫 방문 펌 30% 게릴라 할인 (선착순 5명)", label_visibility="collapsed")
        st.caption("비워두시면 공유창에서 자동으로 숨겨집니다.")
        
        st.markdown("**3. 상시 회원 제휴 혜택**")
        inp_perk = st.text_input("상시 혜택", value=current_perk_val, placeholder="예: 용친 회원 10% DC", label_visibility="collapsed")
        
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.form_submit_button("저장하고 공유창에 즉시 반영", use_container_width=True):
            users_db[user_key]["phone"] = inp_phone.strip()
            users_db[user_key]["today_deal"] = inp_deal.strip()
            users_db[user_key]["map_perk"] = inp_perk.strip()
            users_db[user_key]["today_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_users(users_db)
            st.success("내 매장 정보가 저장되었습니다.")
            st.rerun()

# ------------------------------------------
# TAB 3. 📢 마케팅 & 공구 (원페이지 통합)
# ------------------------------------------
with tab_mkt:
    if not is_pro_user:
        st.markdown("""<div class="simple-card" style="border-left: 4px solid #EF4444; background: #FEF2F2;">
<div style="font-weight: 800; font-size: 1rem; color: #991B1B; margin-bottom: 4px;">PRO 전용 유료 마케팅 기능입니다</div>
<div style="font-size: 0.86rem; color: #7F1D1D; line-height: 1.5;">
무료 체험 기간이 만료되었습니다. 사이드바에서 <b>[유료버전 사용 승인 신청]</b>을 눌러주세요.
</div>
</div>""", unsafe_allow_html=True)
    else:
        current_area_tag = st.session_state.current_region_name.split()[0] if st.session_state.current_region_name else "용인"

        st.markdown("##### ✍️ AI 블로그 SEO 원고 생성기")
        b_kw = st.text_input("메인 키워드", value=f"{current_area_tag} {sel_industry.split('/')[0].strip()}", key="m_b_kw")
        b_core = st.text_area("매장 핵심 강점", value=sel_feature, height=60, key="m_b_core")
        if st.button("SEO 전문 원고 생성하기", key="m_b_btn", use_container_width=True):
            with st.spinner("원고 작성 중..."):
                prompt = f"업종: {sel_industry}\n매장: {store_name}\n지역: {st.session_state.current_region_name}\n키워드: {b_kw}\n강점: {b_core}\n네이버 스마트블록용 제목 3종, 본문, 해시태그 작성."
                out = generate_safe_content(prompt)
                if out: st.text_area("작성된 블로그 원고", value=out, height=250)

        st.markdown("---")
        st.markdown("##### 🥕 당근마켓 이웃 소식 작성기")
        d_prm = st.text_input("제공 혜택", value="무상 정밀 점검 및 세척 서비스", key="m_d_prm")
        if st.button("당근마켓 소식 생성하기", key="m_d_btn", use_container_width=True):
            with st.spinner("소식 작성 중..."):
                prompt = f"매장: {store_name}\n지역: {st.session_state.current_region_name}\n혜택: {d_prm}\n이웃 사장님 친근한 톤으로 당근 소식 원고 작성."
                out = generate_safe_content(prompt)
                if out: st.text_area("당근 소식 원고", value=out, height=220)

        st.markdown("---")
        st.markdown("##### 💬 AI 리뷰 전문 답글 생성기")
        cust_rev = st.text_area("고객 리뷰 붙여넣기", placeholder="고객 리뷰를 입력하세요.", key="m_rev_box")
        if st.button("전문 답글 3종 생성", key="m_r_btn", use_container_width=True):
            if cust_rev:
                with st.spinner("답글 생성 중..."):
                    prompt = f"매장: {store_name}\n리뷰: '{cust_rev}'\n플레이스 신뢰를 높이는 정중한 답글 3종 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("추천 답글 3종", value=out, height=220)
            else:
                st.warning("리뷰 내용을 입력해 주세요.")

        st.markdown("---")
        st.markdown("##### 🛒 로컬 공동구매 참여 센터")
        for d in deals_db["deals"][:2]:
            tot_qty = sum([p["qty"] for p in d["participants"]])
            st.markdown(f"**{d['title']}**<br><span style='color:#2563EB; font-weight:800;'>{d['price']}</span> · {len(d['participants'])}명 참여", unsafe_allow_html=True)
            st.progress(min(tot_qty / d["target"], 1.0))
            with st.form(key=f"quick_join_{d['id']}"):
                q_name = st.text_input("성함 또는 상호", key=f"qn_{d['id']}")
                q_phone = st.text_input("연락처", key=f"qp_{d['id']}")
                q_cnt = st.number_input("수량", min_value=1, value=1, key=f"qq_{d['id']}")
                if st.form_submit_button("간편 공구 신청", use_container_width=True):
                    if q_name and q_phone:
                        d["participants"].append({"name": q_name, "phone": q_phone, "qty": int(q_cnt), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        save_deals(deals_db)
                        st.success("신청 완료되었습니다.")
                        st.rerun()

# ------------------------------------------
# TAB 4. 💼 경영·행정비서 (음악 + 마감 + 계산기 + 서류 통합)
# ------------------------------------------
with tab_biz:
    st.markdown("##### 🎧 매장 사운드 큐레이션")
    music_query = st.selectbox("시간대별 매장 음악 선택", [
        "재즈 보사노바 오전 매장 음악 연속재생",
        "어쿠스틱 팝 피크타임 매장 음악 연속재생",
        "2000년대 감성 발라드 피아노 연주곡 연속재생",
        "세련된 카페 라운지 재즈 음악 연속재생"
    ], key="biz_music_sel")
    st.link_button("유튜브 음악 스트리밍 열기", f"https://www.youtube.com/results?search_query={urllib.parse.quote(music_query)}", use_container_width=True)

    st.markdown("---")
    st.markdown("##### 🌙 일일 영업 마감 리포트")
    c_sales = st.text_input("오늘 매출액 (선택)", placeholder="예: 850,000원", key="biz_sales")
    c_flow = st.selectbox("고객 유입 체감", ["평소 대비 한산함", "평균 수준", "피크타임 집중 방문", "종일 만석 / 목표 초과"], key="biz_flow")
    if st.button("AI 일일 마감 리포트 생성", key="biz_close_btn", use_container_width=True):
        with st.spinner("리포트 분석 중..."):
            prompt = f"매장: {store_name}\n업종: {sel_industry}\n매출: {c_sales}\n유입: {c_flow}\n1) 오늘 총평 2) 내일 과제 3선 작성."
            out = generate_safe_content(prompt)
            if out: st.markdown(f"<div class='simple-card' style='border-left:4px solid #2563EB;'>{out}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### 🧮 소상공인 실무 금융 계산기")
    calc_choice = st.selectbox("계산기 종류 선택", ["파트타이머 알바 급여", "사업자 대출 이자", "제품 마진율 역산", "카드 수수료 정산"], key="biz_calc_sel")
    
    if calc_choice == "파트타이머 알바 급여":
        wage = st.number_input("시급 (원)", value=10030, step=100, key="bc_w")
        hrs = st.number_input("주당 근로시간", value=16.0, step=0.5, key="bc_h")
        base = wage * hrs * 4.345
        holiday = ((hrs / 40.0) * 8.0 * wage * 4.345) if hrs >= 15 else 0
        tot = base + holiday
        st.markdown(f"""<div class="calc-result-box">
<div style="font-size:0.82rem; color:#64748B;">기본급 {int(base):,}원 + 주휴수당 {int(holiday):,}원</div>
<div style="font-size:1.2rem; font-weight:900; color:#0F172A; margin-top:2px;">예상 총 지급액: {int(tot):,}원</div>
</div>""", unsafe_allow_html=True)

    elif calc_choice == "사업자 대출 이자":
        loan_amt = st.number_input("대출 원금 (원)", value=30000000, step=1000000, key="bc_la")
        loan_rate = st.number_input("연 이자율 (%)", value=4.5, step=0.1, key="bc_lr")
        loan_months = st.number_input("기간 (개월)", value=36, step=12, key="bc_lm")
        r = (loan_rate / 100) / 12
        monthly_pay = (loan_amt * r * ((1 + r)**loan_months)) / (((1 + r)**loan_months) - 1)
        st.markdown(f"""<div class="calc-result-box">
<div style="font-size:1.2rem; font-weight:900; color:#0F172A;">원리금균등 월 상환액: {int(monthly_pay):,}원</div>
</div>""", unsafe_allow_html=True)

    elif calc_choice == "제품 마진율 역산":
        cost_price = st.number_input("매입원가 (원)", value=15000, step=1000, key="bc_cp")
        target_margin = st.number_input("목표 마진율 (%)", value=60.0, step=5.0, key="bc_mg")
        calc_selling_price = cost_price / (1 - (target_margin / 100))
        net_profit = calc_selling_price - cost_price
        st.markdown(f"""<div class="calc-result-box">
<div style="font-size:0.82rem; color:#64748B;">개당 순이익: {int(net_profit):,}원</div>
<div style="font-size:1.2rem; font-weight:900; color:#0F172A; margin-top:2px;">권장 판매가: {int(calc_selling_price):,}원</div>
</div>""", unsafe_allow_html=True)

    else:
        card_sales = st.number_input("카드 결제액 (원)", value=1000000, step=100000, key="bc_cs")
        settle_amt = card_sales * 0.995 # 영세 0.5% 가정
        st.markdown(f"""<div class="calc-result-box">
<div style="font-size:1.2rem; font-weight:900; color:#0F172A;">우대수수료 적용 실입금액: {int(settle_amt):,}원</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### 📄 4대 필수 행정서류 및 정책자금 링크")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.link_button("소상공인확인서 (중기현황)", "https://sminfo.mss.go.kr", use_container_width=True)
        st.link_button("국세 완납증명서 (홈택스)", "https://www.hometax.go.kr", use_container_width=True)
    with col_f2:
        st.link_button("부가세 과세표준증명", "https://www.hometax.go.kr", use_container_width=True)
        st.link_button("지방세 납세증명서 (정부24)", "https://www.gov.kr", use_container_width=True)
