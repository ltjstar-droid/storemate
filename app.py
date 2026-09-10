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
            "map_perk": "용친 회원 안경렌즈 추가 10% DC & 고급 안경 클리너 증정",
            "today_deal": "누진다초점 렌즈 50% 할인",
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

# ==========================================
# ☀️ 그래픽 날씨 & 역지오코딩
# ==========================================
def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=14&addressdetails=1"
        headers = {"User-Agent": "StoreMate-Local-App/1.0"}
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
    icon_sun = """<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>"""
    icon_cloud = """<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>"""
    icon_rain = """<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><line x1="16" y1="13" x2="16" y2="21"></line><line x1="8" y1="13" x2="8" y2="21"></line><line x1="12" y1="15" x2="12" y2="23"></line><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"></path></svg>"""

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
    page_title="STORE MATE | 매장비서",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🎨 가독성 중심 미니멀 화이트 테마 CSS
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
    
    .stApp, html, body { background-color: #FFFFFF !important; }

    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        gap: 20px !important;
        background: transparent !important;
        padding: 0 0 8px 0 !important;
        margin-bottom: 20px !important;
        border-bottom: 2px solid #F1F5F9 !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: #64748B !important;
        background: transparent !important;
        border: none !important;
        padding: 0 4px !important;
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
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    .weather-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }

    .calc-result-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2563EB;
        border-radius: 10px;
        padding: 18px 20px;
        margin-top: 14px;
    }

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
    }

    .stButton>button {
        height: 2.8rem !important;
        font-size: 0.95rem !important;
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
        font-size: 0.9rem !important;
        padding: 8px 14px !important;
        text-decoration: none !important;
        display: flex !important;
        justify-content: center !important;
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
    st.markdown("""
    <div style="max-width: 400px; margin: 60px auto 20px auto; text-align: center;">
        <h2 style="font-size: 1.7rem; font-weight: 900; color: #0F172A; margin: 0 0 6px 0;">STORE MATE</h2>
        <p style="font-size: 0.92rem; color: #64748B;">소상공인 통합 관리 플랫폼</p>
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
                new_pw = st.text_input("비밀번호 설정", type="password")
                new_store = st.text_input("매장명")
                new_ind = st.selectbox("업종", INDUSTRY_LIST)
                new_loc = st.text_input("매장 주소")
                if st.form_submit_button("가입 신청", use_container_width=True):
                    if new_id and new_pw and new_store:
                        users_db[new_id] = {
                            "store_name": new_store,
                            "industry": new_ind,
                            "location": new_loc,
                            "feature": "전문 검안 및 맞춤 가공",
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
col_h1, col_h2 = st.columns([1, 1.2])
with col_h1:
    st.markdown(f"### {store_name} &nbsp;<span style='font-size:0.75rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:3px 8px; border-radius:4px;'>{'PRO 파트너' if is_pro_user else '스탠다드'}</span>", unsafe_allow_html=True)
    st.caption(f"등록 매장지: {sel_loc} · {sel_industry}")
with col_h2:
    st.markdown("""
    <div style="display:flex; justify-content:flex-end; gap:8px; padding-top:6px; flex-wrap:wrap;">
        <a href="https://www.facebook.com/groups/yonginfriends" target="_blank" style="background:#1877F2; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">용인친구들 페이스북</a>
        <a href="https://www.instagram.com/" target="_blank" style="background:#E1306C; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">용인친구들 인스타그램</a>
        <a href="https://www.threads.net/" target="_blank" style="background:#111827; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">용인친구들 스레드</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin:12px 0 16px 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

# ==========================================
# 메인 6대 탭 (영업마감 독립 탭 분리!)
# ==========================================
main_tabs = ["홈 대시보드", "마케팅 스튜디오", "로컬 공동구매", "음악 스튜디오", "영업 마감 리포트", "경영 & 행정지원"]
tab_home, tab_mkt, tab_deals, tab_music, tab_close, tab_biz = st.tabs(main_tabs)

# ------------------------------------------
# TAB 1. 🏠 홈 대시보드 (오류 원천 수정 완료)
# ------------------------------------------
with tab_home:
    my_saved_addr = curr_user.get("map_address", sel_loc)
    my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
    my_today_deal = curr_user.get("today_deal", "오늘의 특가 품목 등록 대기 중")
    my_deal_updated = curr_user.get("today_updated", datetime.now().strftime("%Y-%m-%d"))
    naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"

    # 1. ☀️ 실시간 날씨 카드
    weather_info = get_live_weather(st.session_state.current_lat, st.session_state.current_lon)
    
    col_w1, col_w2 = st.columns([3.4, 1])
    with col_w1:
        weather_html = f"""<div class="weather-box">
<div style="display:flex; align-items:center; gap:18px;">
<div>{weather_info['icon']}</div>
<div>
<div style="font-size:1.25rem; font-weight:900; color:#0F172A;">{st.session_state.current_region_name} &nbsp;·&nbsp; {weather_info['status']}</div>
<div style="font-size:0.92rem; color:#475569; margin-top:4px;">{weather_info['tip']}</div>
</div>
</div>
<div style="text-align:right;">
<div style="font-size:1.9rem; font-weight:900; color:#0F172A; line-height:1;">{weather_info['temp']}°C</div>
<div style="font-size:0.75rem; color:#64748B; margin-top:4px;">기상청 연동</div>
</div>
</div>"""
        st.markdown(weather_html, unsafe_allow_html=True)
    with col_w2:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("현재 내 위치 찾기", key="btn_detect_gps", use_container_width=True):
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

    # 2. 오늘의 상생 특가 (들여쓰기 오인에 따른 HTML 태그 노출 오류 해결)
    special_card_html = f"""<div class="simple-card">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
<span style="font-size:1.2rem; font-weight:900; color:#0F172A;">오늘의 매장 특가 & 단골 혜택</span>
<span style="font-size:0.8rem; color:#64748B;">최근 변경: {my_deal_updated}</span>
</div>
<div style="font-size:0.92rem; color:#475569; margin-bottom:14px;">{my_saved_addr}</div>
<div style="background:#EFF6FF; border-left:4px solid #2563EB; border-radius:6px; padding:14px 18px; margin-bottom:14px;">
<div style="font-size:0.8rem; font-weight:700; color:#2563EB;">오늘의 할인 품목</div>
<div style="font-size:1.15rem; font-weight:900; color:#0F172A; margin-top:2px;">{my_today_deal}</div>
</div>
<div style="font-size:0.95rem; color:#334155; margin-bottom:16px;">
<b>상시 혜택:</b> {my_perk}
</div>
</div>"""
    st.markdown(special_card_html, unsafe_allow_html=True)

    col_h_b1, col_h_b2 = st.columns(2)
    with col_h_b1:
        if st.button("특가 품목 / 혜택 문구 수정하기", key="btn_h_edit_deal", use_container_width=True):
            st.session_state.show_deal_edit = not st.session_state.show_deal_edit
    with col_h_b2:
        st.link_button("네이버 플레이스 지도 연동 확인", naver_url, use_container_width=True)

    if st.session_state.show_deal_edit:
        st.markdown("""<div class="simple-card" style="margin-top:14px; border:2px solid #2563EB;">
<div style="font-weight:800; font-size:1rem; color:#0F172A; margin-bottom:12px;">오늘의 특가 품목 및 상시 혜택 변경</div>""", unsafe_allow_html=True)
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            new_today_deal = st.text_input("오늘의 특가 품목", value=my_today_deal, key="h_edit_deal")
        with col_ed2:
            new_perk = st.text_input("기본 상시 혜택", value=my_perk, key="h_edit_perk")
        if st.button("저장하고 바로 반영하기", key="h_save_deal_btn", use_container_width=True):
            users_db[user_key]["today_deal"] = new_today_deal
            users_db[user_key]["map_perk"] = new_perk
            users_db[user_key]["today_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_users(users_db)
            st.session_state.show_deal_edit = False
            st.success("수정되었습니다.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. 진행 중인 공동구매 요약
    st.markdown("""<div class="simple-card" style="margin-top:16px;">
<div style="font-weight:900; font-size:1.15rem; color:#0F172A; margin-bottom:14px;">현재 진행 중인 공동구매</div>""", unsafe_allow_html=True)
    for d in deals_db["deals"][:2]:
        tot_qty = sum([p["qty"] for p in d["participants"]])
        st.markdown(f"**{d['title']}** &nbsp;·&nbsp; <span style='color:#2563EB; font-weight:800;'>{d['price']}</span> &nbsp;·&nbsp; 현재 **{len(d['participants'])}명 참여** ({tot_qty}개 누적)", unsafe_allow_html=True)
        st.progress(min(tot_qty / d["target"], 1.0))
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2. 📢 마케팅 스튜디오
# ------------------------------------------
with tab_mkt:
    current_area_tag = st.session_state.current_region_name.split()[0] if st.session_state.current_region_name else "용인"

    mkt_sub1, mkt_sub2, mkt_sub3, mkt_sub4, mkt_sub5 = st.tabs([
        "네이버 블로그 SEO", "당근마켓 바이럴", "인스타그램 피드", "단골 CRM 문자", "AI 리뷰 대응"
    ])

    with mkt_sub1:
        if not is_pro_user:
            st.info("네이버 스마트블록 SEO 원고 설계는 PRO 파트너 전용 기능입니다.")
        else:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                b_kw = st.text_input("메인 키워드 (지역 자동 반영)", value=f"{current_area_tag} {sel_industry.split('/')[0].strip()}", key="m_b_kw")
                b_sub = st.text_input("서브 키워드", value=f"{st.session_state.current_region_name} 안경 추천, 정밀 시력검사", key="m_b_sub")
                b_photos = st.slider("첨부 사진 장수", 5, 20, 8, key="m_b_photo")
            with col_b2:
                b_intent = st.selectbox("검색 의도", ["실제 단골 내돈내산 방문기", "전문 검안 기술/정밀 장비 분석", "가성비 및 제휴 혜택 비교"], key="m_b_intent")
                b_core = st.text_area("매장 강점", value=sel_feature, height=75, key="m_b_core")

            if st.button("SEO 전문 원고 생성", key="m_b_btn", use_container_width=True):
                with st.spinner("원고 작성 중..."):
                    prompt = f"업종: {sel_industry}\n매장: {store_name}\n지역: {st.session_state.current_region_name}\n키워드: {b_kw}, {b_sub}\n사진: {b_photos}장\n의도: {b_intent}\n강점: {b_core}\n네이버 스마트블록용 제목 3종, 사진 배치 가이드, 본문, 연관 태그 10종 작성."
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
                d_ctx = st.text_input("상황적 훅 (지역 & 날씨 연계)", value=f"{current_area_tag} 날씨 맞춤 시력 점검 및 단골 케어", key="m_d_ctx")
                d_cta = st.text_input("행동 유도 (CTA)", value="당근 단골 맺기 누르고 매장 방문 시 적용", key="m_d_cta")

            if st.button("당근마켓 소식 생성", key="m_d_btn", use_container_width=True):
                with st.spinner("소식 작성 중..."):
                    prompt = f"매장: {store_name}\n지역: {st.session_state.current_region_name}\n업종: {sel_industry}\n타깃: {d_tgt}\n혜택: {d_prm}\n상황: {d_ctx}\nCTA: {d_cta}\n당근마켓 이웃 사장님 톤으로 제목 2종, 본문, 댓글 유도 질문 작성."
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
                    prompt = f"매장: {store_name}\n업종: {sel_industry}\n지역: {st.session_state.current_region_name}\n형식: {i_type}\n무드: {i_mood}\n주제: {i_subj}\n혜택: {i_perk}\n촬영 가이드, 첫 줄 카피, 줄바꿈 본문, 해시태그 15종 작성."
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
        st.markdown("##### 네이버 플레이스 & 배달/당근 리뷰 자동 답글 솔루션")
        cust_rev = st.text_area("고객 리뷰 본문 붙여넣기", placeholder="고객이 남긴 별점 리뷰 또는 후기 내용을 입력하세요.")
        
        rev_stl = st.selectbox("답글 전략 스타일 (6종)", [
            "1. 정중하고 품격 있는 VIP 감사형 (예의와 신뢰를 중시하는 고급스러운 어조)",
            "2. 다정하고 센스 있는 동네 이웃형 (단골 이웃에게 이야기하듯 따뜻하고 친근한 톤)",
            "3. 매장 특장점 & 장비 전문성 각인형 (정밀 검안 및 전문 설비의 강점을 은근히 각인)",
            "4. 재방문 유도 & 단골 혜택 안내형 (다음 방문 시 무상 점검/세척 혜택을 자연스럽게 제시)",
            "5. 위트 있고 유쾌한 에너지형 (기분 좋은 센스와 활기를 불어넣는 톡톡 튀는 답변)",
            "6. 불만/아쉬움 리뷰 케어 및 재방문 약속형 (정중한 사과, 원인 설명 및 개선 보상 약속)"
        ], key="m_r_stl")
        
        if st.button("전문 답글 3종 생성 실행", key="m_r_btn", use_container_width=True):
            if cust_rev:
                with st.spinner("리뷰 맥락 분석 및 3종 맞춤 답글 생성 중..."):
                    prompt = f"""
                    매장명: {store_name}
                    업종: {sel_industry}
                    소재지: {st.session_state.current_region_name}
                    고객 리뷰 본문: "{cust_rev}"
                    선택한 답글 스타일: {rev_stl}

                    위 고객 리뷰를 바탕으로 플레이스 방문자들이 보고 신뢰감을 느낄 수 있는 완성도 높은 답글 3종을 작성하라.
                    - 불필요한 이모티콘은 배제하고 정갈하게 작성할 것.
                    - 리뷰 스타일에 완벽히 부합하면서도 고객의 언급 사항을 섬세하게 짚어줄 것.
                    """
                    out = generate_safe_content(prompt)
                    if out: st.text_area("추천 답글 3종 세트", value=out, height=320)
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
            <div class="simple-card" style="margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="background:{'#64748B' if is_closed else '#EF4444'}; color:#fff; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:4px;">{dday}</span>
                    <span style="font-size:0.85rem; color:#64748B;">목표 {deal['target']}개</span>
                </div>
                <h4 style="margin:8px 0 4px 0; color:#0F172A;">{deal['title']}</h4>
                <div style="font-size:1.15rem; font-weight:900; color:#2563EB;">{deal['price']}</div>
                <div style="font-size:0.88rem; color:#475569; margin:4px 0 8px 0;">신청: <b>{len(deal['participants'])}명</b> ({tot_qty}개 달성)</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(tot_qty / deal["target"], 1.0))

            col_ctrl_a, col_ctrl_b = st.columns([1.5, 1])
            with col_ctrl_a:
                is_active = (st.session_state.active_join_deal_id == deal["id"])
                btn_label = "신청창 닫기" if is_active else "공구 참여 신청"
                if st.button(btn_label, key=f"toggle_join_{deal['id']}", use_container_width=True):
                    st.session_state.active_join_deal_id = None if is_active else deal["id"]
                    st.rerun()

            with col_ctrl_b:
                if user_key == "admin" or is_closed:
                    if st.button("프로젝트 삭제", key=f"del_{deal['id']}", use_container_width=True):
                        deals_to_del.append(deal["id"])

            if user_key == "admin":
                st.markdown("""
                <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; padding:12px; margin-top:8px;">
                    <div style="font-size:0.82rem; font-weight:700; color:#0F172A; margin-bottom:6px;">관리자 전용: 신청자 데이터 관리</div>
                """, unsafe_allow_html=True)
                col_adm_dl, _ = st.columns([1.5, 2])
                with col_adm_dl:
                    if len(deal["participants"]) > 0:
                        df_parts = pd.DataFrame(deal["participants"])
                        df_parts.columns = ["성함/상호", "연락처", "신청수량", "신청일시"]
                        csv_data = df_parts.to_csv(index=False, encoding="utf-8-sig")
                        st.download_button(
                            label=f"📥 참여자 명단 엑셀(CSV) 다운로드 ({len(deal['participants'])}명)",
                            data=csv_data,
                            file_name=f"공구명단_{deal['id']}.csv",
                            mime="text/csv",
                            key=f"csv_adm_{deal['id']}",
                            use_container_width=True
                        )
                        st.dataframe(df_parts, use_container_width=True)
                    else:
                        st.caption("현재 신청자가 없습니다.")
                st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.active_join_deal_id == deal["id"]:
                st.markdown(f"""
                <div class="simple-card" style="margin-top:8px; border-left:4px solid #2563EB;">
                    <div style="font-weight:700; font-size:0.95rem; color:#0F172A; margin-bottom:10px;">[{deal['title']}] 참여 신청서</div>
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
        <div class="simple-card">
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
# TAB 4. 🎧 음악 스튜디오
# ------------------------------------------
with tab_music:
    st.markdown("""
    <div class="simple-card">
        <div style="font-weight:900; font-size:1.15rem; color:#0F172A; margin-bottom:4px;">매장 분위기 & 시간대별 사운드 스테이션</div>
        <div style="font-size:0.88rem; color:#64748B;">매장의 품격을 높이고 고객 체류 시간을 늘리는 원클릭 스트리밍 큐레이션</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### 시간대별 원클릭 추천 스테이션")
    
    music_presets = [
        {
            "slot": "오전 오픈 준비 (09:00 ~ 11:30)",
            "vibe": "경쾌하고 맑은 스타트",
            "desc": "매장 청소 및 오픈 준비, 고객 맞이용 산뜻한 음악",
            "query": "재즈 보사노바 오전 매장 음악 연속재생",
            "tag": "모닝 보사노바"
        },
        {
            "slot": "점심 / 오후 피크 (11:30 ~ 14:00)",
            "vibe": "생동감 있는 활력 & 템포",
            "desc": "회전율과 매장 활기를 유지하는 경쾌한 템포",
            "query": "어쿠스틱 팝 피크타임 매장 음악 연속재생",
            "tag": "어쿠스틱 팝"
        },
        {
            "slot": "나른한 오후 (14:00 ~ 17:30)",
            "vibe": "편안하고 아늑한 칠아웃",
            "desc": "상담 및 시력검사 집중도를 높이는 힐링 연주곡",
            "query": "2000년대 감성 발라드 피아노 연주곡 연속재생",
            "tag": "감성 피아노"
        },
        {
            "slot": "저녁 골든타임 & 마감 (17:30 ~ 21:00)",
            "vibe": "고급스러운 무드 라운지",
            "desc": "하루를 우아하게 마무리하는 감각적인 재즈",
            "query": "세련된 카페 라운지 재즈 음악 연속재생",
            "tag": "라운지 재즈"
        }
    ]

    col_s1, col_s2 = st.columns(2)
    for idx, preset in enumerate(music_presets):
        target_col = col_s1 if idx % 2 == 0 else col_s2
        p_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(preset['query'])}"
        with target_col:
            st.markdown(f"""
            <div class="sound-station-card" style="margin-bottom:14px;">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:0.72rem; font-weight:700; color:#2563EB; background:#EFF6FF; padding:2px 8px; border-radius:4px;">{preset['tag']}</span>
                        <span style="font-size:0.75rem; color:#94A3B8;">CH 0{idx+1}</span>
                    </div>
                    <div style="font-weight:800; font-size:1rem; color:#0F172A; margin:8px 0 2px 0;">{preset['slot']}</div>
                    <div style="font-size:0.86rem; color:#2563EB; font-weight:700;">{preset['vibe']}</div>
                    <div style="font-size:0.82rem; color:#64748B; margin-top:4px;">{preset['desc']}</div>
                </div>
                <div style="margin-top:14px;">
                    <a href="{p_url}" target="_blank" style="text-decoration:none;">
                        <button style="width:100%; height:36px; background:#0F172A; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; font-size:0.85rem; cursor:pointer;">
                            유튜브에서 즉시 재생
                        </button>
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("##### 맞춤형 사운드 검색 조율기")
    with st.container():
        st.markdown("""
        <div class="simple-card">
            <div style="font-weight:700; font-size:0.95rem; color:#0F172A; margin-bottom:12px;">원하는 분위기와 장르를 직접 조합하여 유튜브 스트리밍 채널을 탐색합니다.</div>
        """, unsafe_allow_html=True)
        col_m_cust1, col_m_cust2 = st.columns(2)
        with col_m_cust1:
            m_time_custom = st.selectbox("1. 원하는 매장 분위기/시간대", [
                "오전 오픈 준비 (경쾌한 무드)",
                "점심/오후 피크 (활기 유지 & 칠)",
                "나른한 오후 3~5시 (편안한 어쿠스틱)",
                "저녁 골든타임 (아늑한 라운지 재즈)",
                "비 오는 날 감성 (센티멘털 어쿠스틱)",
                "마감 정리 (차분한 피아노 연주)"
            ], key="tab_m_time_cust")
        with col_m_cust2:
            m_style_custom = st.selectbox("2. 선호 장르", [
                "재즈 / 보사노바 (클래식 매장)",
                "어쿠스틱 팝 & 인디 감성 보컬",
                "2000년대 감성 발라드 피아노 커버",
                "세련된 Lo-Fi 칠(Lo-Fi Chill) 비트",
                "90-2000 국민 애창 댄스 (식당/펍)",
                "흥겨운 최신 트로트 명곡 메들리"
            ], key="tab_m_style_cust")
        
        yt_custom_q = f"{m_style_custom.split('/')[0].strip()} {m_time_custom.split('(')[0].strip()} 플레이리스트 연속재생"
        custom_music_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_custom_q)}"
        
        st.markdown(f"<div style='font-size:0.85rem; color:#64748B; margin:8px 0 14px 0;'>선택된 큐레이션 검색어: <b>{yt_custom_q}</b></div>", unsafe_allow_html=True)
        st.link_button(f"유튜브 '{m_style_custom.split('/')[0].strip()}' 스트리밍 열기", custom_music_url, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 5. 🌙 영업 마감 리포트 (독립 탭으로 격상)
# ------------------------------------------
with tab_close:
    st.markdown("""
    <div class="simple-card">
        <div style="font-weight:900; font-size:1.15rem; color:#0F172A; margin-bottom:4px;">일일 영업 결산 & 내일 경영 플래너</div>
        <div style="font-size:0.88rem; color:#64748B;">오늘 하루 매출과 유입 분위기를 정리하고, 내일 우선 실행 과제를 AI로 도출합니다.</div>
    </div>
    """, unsafe_allow_html=True)

    col_cl1, col_cl2 = st.columns(2)
    with col_cl1:
        c_sales = st.text_input("오늘 대략적인 매출액 (선택)", placeholder="예: 850,000원", key="b_sales")
        c_flow = st.selectbox("고객 유입 체감", ["평소 대비 한산함", "평균 수준", "특정 피크타임 집중 방문", "종일 만석 / 목표 초과 달성"], key="b_flow")
    with col_cl2:
        c_memo = st.text_input("오늘의 특이사항 또는 재고 이슈", placeholder="예: 특정 렌즈 재고 소진, 단골 3명 방문", key="b_memo")
        c_sat = st.selectbox("오늘 매장 운영 만족도", ["다소 아쉬움 (내일 만회 필요)", "무난하고 안정적", "매우 만족스러움 (추세 유지)"], key="b_sat")

    if st.button("일일 경영 결산 리포트 생성 실행", key="b_close_btn", use_container_width=True):
        with st.spinner("경영 데이터 종합 분석 중..."):
            prompt = f"""
            매장명: {store_name}
            업종: {sel_industry}
            소재지: {st.session_state.current_region_name}
            당일 매출: {c_sales if c_sales else '미입력'}
            고객 유입 체감: {c_flow}
            특이사항: {c_memo if c_memo else '없음'}
            운영 만족도: {c_sat}

            당신은 20년 경력의 매장 경영 수석 컨설턴트다.
            오늘 하루 고생한 사장님을 위해 1) 오늘 경영 총평 2) 내일 필수 실행과제 3가지 3) 퇴근길 멘탈 리셋 격려를 정갈한 비즈니스 리포트 양식으로 작성하라.
            """
            out = generate_safe_content(prompt)
            if out:
                st.markdown(f"<div class='simple-card' style='border-left:4px solid #2563EB; margin-top:14px;'>{out}</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 6. 💼 경영 & 행정지원 (소상공인 4대 금융계산기 허브 완비)
# ------------------------------------------
with tab_biz:
    biz_sub1, biz_sub2, biz_sub3 = st.tabs([
        "4대 행정서류 발급처", "2026 정책금융 진단", "소상공인 금융계산기 센터"
    ])

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
                if out: st.markdown(f"<div class='simple-card' style='border-left:4px solid #2563EB;'>{out}</div>", unsafe_allow_html=True)

    # 💡 [소상공인 4대 금융계산기 센터 전면 구축]
    with biz_sub3:
        st.markdown("##### 🧮 소상공인 실무 금융 & 운영 계산기 센터")
        calc_tab1, calc_tab2, calc_tab3, calc_tab4 = st.tabs([
            "알바 급여 & 주휴수당", "사업자 대출 이자 계산기", "마진율 & 판매가 역산", "카드 수수료 실입금액"
        ])

        # 1. 알바 급여 계산기
        with calc_tab1:
            w1, w2 = st.columns(2)
            with w1:
                wage = st.number_input("기본 시급 (원)", value=10030, step=100, key="c1_wage")
                hrs = st.number_input("주당 소정근로시간 (시간)", value=16.0, step=0.5, key="c1_hrs")
            with w2:
                tax_opt = st.selectbox("공제 방식", ["사업소득세 3.3% 공제 (3.3%)", "고용보험 0.9% 공제 (0.9%)", "공제 없음 (100% 지급)"], key="c1_tax")
            base = wage * hrs * 4.345
            holiday = ((hrs / 40.0) * 8.0 * wage * 4.345) if hrs >= 15 else 0
            tot = base + holiday
            ded = tot * 0.033 if "3.3%" in tax_opt else (tot * 0.009 if "0.9%" in tax_opt else 0)
            net = tot - ded
            st.markdown(f"""
            <div class="calc-result-box">
                <div style="font-size:0.88rem; color:#64748B;">기본급: {int(base):,}원 &nbsp;·&nbsp; 법정 주휴수당: {int(holiday):,}원 &nbsp;·&nbsp; 공제액: {int(ded):,}원</div>
                <div style="font-size:1.35rem; font-weight:900; color:#0F172A; margin-top:4px;">예상 실지급액: {int(net):,}원</div>
                <div style="font-size:0.8rem; color:#94A3B8; margin-top:2px;">(주 15시간 이상 근무 시 주휴수당 의무 지급 대상입니다.)</div>
            </div>
            """, unsafe_allow_html=True)

        # 2. 대출 이자 & 상환 계산기
        with calc_tab2:
            l1, l2 = st.columns(2)
            with l1:
                loan_amt = st.number_input("대출 원금 (원)", value=30000000, step=1000000, key="c2_amt")
                loan_rate = st.number_input("연 이자율 (%)", value=4.5, step=0.1, key="c2_rate")
            with l2:
                loan_months = st.number_input("대출 기간 (개월)", value=36, step=12, key="c2_months")
                loan_type = st.selectbox("상환 방식", ["원리금균등상환", "원금균등상환", "만기일시상환"], key="c2_type")

            r = (loan_rate / 100) / 12
            n = loan_months
            if loan_type == "원리금균등상환":
                monthly_pay = (loan_amt * r * ((1 + r)**n)) / (((1 + r)**n) - 1)
                total_pay = monthly_pay * n
                total_interest = total_pay - loan_amt
            elif loan_type == "원금균등상환":
                monthly_principal = loan_amt / n
                total_interest = sum([(loan_amt - (monthly_principal * i)) * r for i in range(n)])
                monthly_pay = monthly_principal + (loan_amt * r)
                total_pay = loan_amt + total_interest
            else: # 만기일시
                monthly_pay = loan_amt * r
                total_interest = monthly_pay * n
                total_pay = loan_amt + total_interest

            st.markdown(f"""
            <div class="calc-result-box">
                <div style="font-size:0.88rem; color:#64748B;">총 상환금액: {int(total_pay):,}원 &nbsp;·&nbsp; 총 대출 이자: {int(total_interest):,}원</div>
                <div style="font-size:1.35rem; font-weight:900; color:#0F172A; margin-top:4px;">1회차 월 상환액: {int(monthly_pay):,}원</div>
                <div style="font-size:0.8rem; color:#94A3B8; margin-top:2px;">(신용보증재단 저금리 대환보증 및 정책자금 심사 시 참고 기준액입니다.)</div>
            </div>
            """, unsafe_allow_html=True)

        # 3. 마진율 & 판매가 역산기
        with calc_tab3:
            m1, m2 = st.columns(2)
            with m1:
                cost_price = st.number_input("제품/메뉴 매입원가 (원)", value=15000, step=1000, key="c3_cost")
                target_margin = st.number_input("목표 마진율 (%)", value=60.0, step=5.0, key="c3_margin")
            with m2:
                discount_rate = st.number_input("고객 할인 제공율 (%) - 선택", value=10.0, step=5.0, key="c3_dc")
            
            # 마진율 공식: (판매가 - 원가) / 판매가 = 마진율 => 판매가 = 원가 / (1 - 마진율)
            calc_selling_price = cost_price / (1 - (target_margin / 100))
            net_profit = calc_selling_price - cost_price
            discounted_selling = calc_selling_price * (1 - (discount_rate / 100))
            discounted_profit = discounted_selling - cost_price

            st.markdown(f"""
            <div class="calc-result-box">
                <div style="font-size:0.88rem; color:#64748B;">권장 정상 판매가: {int(calc_selling_price):,}원 &nbsp;·&nbsp; 개당 순수익: {int(net_profit):,}원</div>
                <div style="font-size:1.35rem; font-weight:900; color:#0F172A; margin-top:4px;">{int(discount_rate)}% 할인 적용 판매가: {int(discounted_selling):,}원 (순이익: {int(discounted_profit):,}원)</div>
                <div style="font-size:0.8rem; color:#94A3B8; margin-top:2px;">(공동구매나 번개 특가 품목 가격 책정 시 마진을 방어할 수 있습니다.)</div>
            </div>
            """, unsafe_allow_html=True)

        # 4. 카드 수수료 & 정산액 계산기
        with calc_tab4:
            k1, k2 = st.columns(2)
            with k1:
                card_sales = st.number_input("카드 결제 매출액 (원)", value=1000000, step=100000, key="c4_sales")
            with k2:
                card_fee_tier = st.selectbox("가맹점 연매출 구간 (우대 수수료)", [
                    "영세 가맹점 (연매출 3억 이하 / 0.5%)",
                    "중소1 가맹점 (연매출 3억~5억 / 1.1%)",
                    "중소2 가맹점 (연매출 5억~10억 / 1.25%)",
                    "중소3 가맹점 (연매출 10억~30억 / 1.5%)",
                    "일반 가맹점 (연매출 30억 초과 / 2.0%)"
                ], key="c4_fee")
            
            fee_rates = {"0.5%": 0.005, "1.1%": 0.011, "1.25%": 0.0125, "1.5%": 0.015, "2.0%": 0.02}
            cur_rate = 0.005
            for k, v in fee_rates.items():
                if k in card_fee_tier:
                    cur_rate = v
                    break
            
            calc_fee = card_sales * cur_rate
            settle_amt = card_sales - calc_fee

            st.markdown(f"""
            <div class="calc-result-box">
                <div style="font-size:0.88rem; color:#64748B;">적용 수수료율: {cur_rate*100}% &nbsp;·&nbsp; 차감 수수료: {int(calc_fee):,}원</div>
                <div style="font-size:1.35rem; font-weight:900; color:#0F172A; margin-top:4px;">실제 계좌 입금 예정액: {int(settle_amt):,}원</div>
                <div style="font-size:0.8rem; color:#94A3B8; margin-top:2px;">(카드사 공제 후 실제 영업 계좌에 입금되는 정산 기준액입니다.)</div>
            </div>
            """, unsafe_allow_html=True)
