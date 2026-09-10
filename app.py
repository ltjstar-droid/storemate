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
CUSTOMERS_DB_FILE = "customers_db.json"

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

def load_customers():
    if os.path.exists(CUSTOMERS_DB_FILE):
        try:
            with open(CUSTOMERS_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return [
        {"phone_last": "1234", "name": "김민수", "visits": 3, "points": 3000, "memo": "변색렌즈 상담"},
        {"phone_last": "5678", "name": "이지영", "visits": 5, "points": 5000, "memo": "아큐브 렌즈 정기고객"}
    ]

def save_customers(data):
    try:
        with open(CUSTOMERS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

st.set_page_config(
    page_title="STORE MATE | 캐시노트형 매장비서",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🎨 [캐시노트 스타일 모바일 피드 CSS]
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
    .stApp { background-color: #F3F4F6 !important; }

    /* 캐시노트 상단 앱 헤더 */
    .cashnote-header {
        background: #FFFFFF;
        padding: 16px 20px;
        border-radius: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .store-brand-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #111827;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .store-plan-pill {
        font-size: 0.72rem;
        font-weight: 700;
        background: #EFF6FF;
        color: #2563EB;
        padding: 3px 8px;
        border-radius: 12px;
    }

    /* 알림 배너 */
    .alert-banner {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #FFFFFF;
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .alert-banner * { color: #FFFFFF !important; }

    /* 캐시노트 5대 퀵 액션 그리드 */
    .quick-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        margin-bottom: 16px;
    }
    .quick-btn {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 12px 6px;
        text-align: center;
        font-size: 0.8rem;
        font-weight: 700;
        color: #374151;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }

    /* 캐시노트 피드 카드 */
    .feed-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    .feed-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 4px;
    }
    .feed-subtitle {
        font-size: 0.85rem;
        color: #6B7280;
        margin-bottom: 14px;
    }

    /* SNS 채널 도크 바 */
    .sns-channel-bar {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }
    .btn-channel {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        text-decoration: none !important;
    }
    .btn-fb { background: #1877F2; color: #FFFFFF !important; }
    .btn-insta { background: #E1306C; color: #FFFFFF !important; }
    .btn-threads { background: #111827; color: #FFFFFF !important; }

    /* 정책지원 카드 */
    .policy-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 12px;
        margin-top: 10px;
    }
    .policy-box {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* 공통 버튼 */
    .stButton>button {
        height: 2.8rem !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
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
customers_db = load_customers()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# ==========================================
# 로그인 화면
# ==========================================
if not st.session_state.logged_in_user:
    st.markdown("""
    <div style="max-width: 420px; margin: 50px auto 20px auto; text-align: center;">
        <h2 style="font-size: 1.7rem; font-weight: 900; color: #111827; margin: 0 0 6px 0;">STORE MATE</h2>
        <p style="font-size: 0.92rem; color: #6B7280;">캐시노트형 소상공인 올인원 경영 솔루션</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.02, 0.96, 0.02])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["로그인", "신규 사업자 등록"])
        with auth_tab1:
            with st.form("login_form"):
                login_id = st.text_input("아이디 또는 사업자 연락처")
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
                new_id = st.text_input("아이디 (연락처 권장)")
                new_pw = st.text_input("비밀번호 설정", type="password")
                new_store = st.text_input("매장 상호명")
                new_ind = st.selectbox("업종 선택", INDUSTRY_LIST)
                new_loc = st.text_input("매장 주소")
                if st.form_submit_button("등록 신청", use_container_width=True):
                    if new_id and new_pw and new_store:
                        users_db[new_id] = {
                            "store_name": new_store,
                            "industry": new_ind,
                            "location": new_loc,
                            "feature": "전문 상담 및 정밀 서비스",
                            "map_address": new_loc,
                            "map_perk": "용친 회원 방문 시 특별 혜택 제공",
                            "today_deal": "오늘의 특가 품목 준비 중",
                            "today_updated": datetime.now().strftime("%Y-%m-%d"),
                            "pw": new_pw,
                            "is_pro": False,
                            "pro_status": "미신청" 
                        }
                        save_users(users_db)
                        st.success("등록 완료! 로그인해 주세요.")
    st.stop()

# ==========================================
# 메인 피드 대시보드
# ==========================================
user_key = st.session_state.logged_in_user
curr_user = users_db.get(user_key, {})
store_name = curr_user.get("store_name", "드림안경 송전점")
sel_industry = curr_user.get("industry", INDUSTRY_LIST[0])
sel_loc = curr_user.get("location", "용인시 처인구 이동읍 경기동로 725")
sel_feature = curr_user.get("feature", "독일식 초정밀 시력검사")
is_pro_user = curr_user.get("is_pro", False)

with st.sidebar:
    st.markdown("### 매장 계정 관리")
    st.markdown(f"**{store_name}**")
    if is_pro_user:
        st.success("PRO 파트너 등급 활성화")
    else:
        st.caption("스탠다드 회원")
        if st.button("PRO 권한 신청", use_container_width=True):
            curr_user["pro_status"] = "대기중"
            users_db[user_key] = curr_user
            save_users(users_db)
            st.rerun()

    if user_key == "admin":
        st.markdown("---")
        st.markdown("### 관리자 회원 승인 센터")
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

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

SYSTEM_DIRECTIVE = """
너는 국내 최상위 소상공인 경영 및 로컬 마케팅 수석 디렉터다.
이모티콘 남발은 철저히 배제하고, 캐시노트나 토스처럼 정갈하고 전문적인 비즈니스 포맷으로 실무 원고와 데이터를 제공한다.
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
            st.error("엔진 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.")
            return None

# ==========================================
# 1. 캐시노트 스타일 앱 상단 헤더 & 알림
# ==========================================
st.markdown(f"""
<div class="cashnote-header">
    <div class="store-brand-title">
        {store_name} ▾ <span class="store-plan-pill">{'PRO' if is_pro_user else 'FREE'}</span>
    </div>
    <div style="font-size: 0.85rem; color: #4B5563; font-weight: 600;">
        {sel_loc.split()[1] if len(sel_loc.split())>1 else '용인'}
    </div>
</div>
""", unsafe_allow_html=True)

# 💡 [신규 기능 1] 출근길 1분 날씨 & 요일 마케팅 알림 브리핑
st.markdown(f"""
<div class="alert-banner">
    <div>
        <div style="font-size:0.75rem; color:#94A3B8; font-weight:700; text-transform:uppercase;">TODAY's BRIEFING</div>
        <div style="font-size:0.95rem; font-weight:700; margin-top:2px;">
            오늘 목요일, 기온 변화에 맞춰 단골 안부 문자와 번개 특가를 활성화하세요.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 소셜 미디어 도크 바
st.markdown("""
<div class="sns-channel-bar">
    <div style="font-size:0.85rem; font-weight:700; color:#374151;">용인친구들 공식 채널</div>
    <div>
        <a href="https://www.facebook.com/groups/yonginfriends" target="_blank" class="btn-channel btn-fb">페이스북</a>
        <a href="https://www.instagram.com/" target="_blank" class="btn-channel btn-insta">인스타그램</a>
        <a href="https://www.threads.net/" target="_blank" class="btn-channel btn-threads">스레드</a>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. 메인 피드 섹션 1: 상생아지트 & 데일리 특가 카드
# ==========================================
my_saved_addr = curr_user.get("map_address", sel_loc)
my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
my_today_deal = curr_user.get("today_deal", "오늘의 특가 품목 등록 대기 중")
my_deal_updated = curr_user.get("today_updated", datetime.now().strftime("%Y-%m-%d"))
naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"

st.markdown(f"""
<div class="feed-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div class="feed-title">오늘의 상생아지트 & 번개 특가</div>
        <span style="font-size:0.75rem; color:#6B7280;">갱신: {my_deal_updated}</span>
    </div>
    <div class="feed-subtitle">{my_saved_addr}</div>
    <div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:10px; padding:12px 14px; margin-bottom:12px;">
        <div style="font-size:0.75rem; font-weight:700; color:#B45309; text-transform:uppercase;">TODAY'S SPECIAL</div>
        <div style="font-size:1.05rem; font-weight:800; color:#92400E; margin-top:2px;">{my_today_deal}</div>
    </div>
    <div style="font-size:0.88rem; color:#4B5563; margin-bottom:12px;"><b>상시 제휴 혜택:</b> {my_perk}</div>
    <a href="{naver_url}" target="_blank" style="text-decoration:none;">
        <button style="width:100%; height:38px; background:#03C75A; color:#FFFFFF; border:none; border-radius:8px; font-weight:700; cursor:pointer;">
            네이버 플레이스 지도 연동 확인
        </button>
    </a>
</div>
""", unsafe_allow_html=True)

with st.expander("오늘의 번개 특가 / 혜택 직접 변경하기", expanded=False):
    col_ed1, col_ed2 = st.columns(2)
    with col_ed1:
        new_today_deal = st.text_input("오늘의 특가 품목", value=my_today_deal, key="feed_td_deal")
    with col_ed2:
        new_perk = st.text_input("기본 상시 혜택", value=my_perk, key="feed_td_perk")
    if st.button("특가 및 혜택 즉시 반영", key="btn_feed_save_deal", use_container_width=True):
        users_db[user_key]["today_deal"] = new_today_deal
        users_db[user_key]["map_perk"] = new_perk
        users_db[user_key]["today_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_users(users_db)
        st.success("실시간 매장 혜택이 업데이트되었습니다.")
        st.rerun()

# ==========================================
# 3. 메인 피드 섹션 2: 실시간 로컬 공동구매 허브
# ==========================================
st.markdown("""
<div class="feed-card">
    <div class="feed-title">실시간 로컬 공동구매 센터</div>
    <div class="feed-subtitle">소상공인 핫딜 및 사업장 소모품 도매 공동 발주</div>
</div>
""", unsafe_allow_html=True)

deal_tab1, deal_tab2, deal_tab3 = st.tabs(["진행 중인 핫딜", "소모품 도매 발주", "신규 공구 제안"])

def get_dday(deadline_str):
    try:
        d_date = datetime.strptime(deadline_str, "%Y-%m-%d")
        delta = (d_date - datetime.now()).days
        return f"D-{delta}일" if delta > 0 else ("오늘 마감" if delta == 0 else "마감")
    except Exception:
        return "진행 중"

with deal_tab1:
    deals_to_del = []
    for d_idx, deal in enumerate(deals_db["deals"]):
        tot_qty = sum([p["qty"] for p in deal["participants"]])
        dday = get_dday(deal["deadline"])
        is_closed = (dday == "마감")
        
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:12px; padding:16px; margin-bottom:12px;">
            <span style="background:{'#6B7280' if is_closed else '#EF4444'}; color:#fff; font-size:0.75rem; font-weight:700; padding:2px 6px; border-radius:4px;">{dday}</span>
            <h4 style="margin:8px 0; color:#111827;">{deal['title']}</h4>
            <div style="font-size:1rem; font-weight:800; color:#2563EB;">{deal['price']}</div>
            <div style="font-size:0.85rem; color:#6B7280; margin-top:4px;">참여: {len(deal['participants'])}명 (누적 {tot_qty}개 / 목표 {deal['target']}개)</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(tot_qty / deal["target"], 1.0))
        
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if len(deal["participants"]) > 0:
                df_parts = pd.DataFrame(deal["participants"])
                df_parts.columns = ["성함/상호", "연락처", "신청수량", "신청일시"]
                csv_file = df_parts.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label=f"📥 참여자 명단 엑셀(CSV) 다운로드",
                    data=csv_file,
                    file_name=f"공구명단_{deal['id']}.csv",
                    mime="text/csv",
                    key=f"csv_dl_{deal['id']}",
                    use_container_width=True
                )
        with c_act2:
            if user_key == "admin" or is_closed:
                if st.button("공구 프로젝트 영구 삭제", key=f"del_d_{deal['id']}", use_container_width=True):
                    deals_to_del.append(deal["id"])
                    
        with st.form(key=f"join_form_{deal['id']}"):
            st.markdown("###### 참여 신청")
            p_n = st.text_input("성함 또는 상호", key=f"p_n_{deal['id']}")
            p_p = st.text_input("연락처", key=f"p_p_{deal['id']}")
            p_q = st.number_input("수량", min_value=1, max_value=100, value=1, step=1, key=f"p_q_{deal['id']}")
            if st.form_submit_button("참여 확정하기", use_container_width=True):
                if p_n and p_p:
                    deal["participants"].append({"name": p_n, "phone": p_p, "qty": int(p_q), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    save_deals(deals_db)
                    st.success("신청되었습니다.")
                    st.rerun()
                else:
                    st.warning("정보를 입력하세요.")
        st.markdown("<hr>", unsafe_allow_html=True)
        
    if deals_to_del:
        deals_db["deals"] = [d for d in deals_db["deals"] if d["id"] not in deals_to_del]
        save_deals(deals_db)
        st.rerun()

with deal_tab2:
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:12px; padding:16px;">
        <h4 style="margin:0;">카드단말기 영수증 롤페이퍼 (50롤 1박스)</h4>
        <p style="color:#4B5563; font-size:0.9rem; margin-top:6px;">시중가 38,000원 ➡️ <b>공구가 23,500원 (무료배송)</b></p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("소모품 공동발주 접수", key="feed_b2b_btn", use_container_width=True):
        st.success("발주 신청이 접수되었습니다.")

with deal_tab3:
    c_n = st.text_input("제안 상품명", key="feed_prop_name")
    c_q = st.number_input("목표 수량", min_value=1, max_value=1000, value=30, step=1, key="feed_prop_qty")
    c_d = st.text_input("제안 공구가", key="feed_prop_price")
    c_day = st.slider("진행 일수", min_value=3, max_value=30, value=7, key="feed_prop_days")
    if st.button("공구 등록 신청", key="feed_prop_btn", use_container_width=True):
        if c_n and c_d:
            deals_db["deals"].append({
                "id": f"deal_{int(time.time())}",
                "title": f"[{store_name}] {c_n}",
                "price": f"{c_d} (단독 특가)",
                "target": int(c_q),
                "deadline": (datetime.now() + timedelta(days=c_day)).strftime("%Y-%m-%d"),
                "participants": []
            })
            save_deals(deals_db)
            st.success("공동구매 프로젝트가 개설되었습니다.")
            st.rerun()

# ==========================================
# 4. 메인 피드 섹션 3: 단골 관리 간이 장부 (신규 기능 2)
# ==========================================
st.markdown("""
<div class="feed-card">
    <div class="feed-title">방문 고객 포인트 & 스탬프 간이 장부</div>
    <div class="feed-subtitle">전화번호 뒷자리 4자리로 관리하는 심플 고객 리텐션 데이터</div>
</div>
""", unsafe_allow_html=True)

col_cust1, col_cust2 = st.columns([1.2, 1])
with col_cust1:
    st.dataframe(pd.DataFrame(customers_db), use_container_width=True)
with col_cust2:
    with st.form("add_customer_form"):
        st.markdown("###### 신규 방문 등록 / 적립")
        c_last = st.text_input("전화번호 뒷자리", max_chars=4, placeholder="예: 6054")
        c_name = st.text_input("고객 성함/별칭", placeholder="예: 단골 이대표님")
        c_memo = st.text_input("방문 메모", placeholder="예: 누진다초점 상담 완료")
        if st.form_submit_button("방문 기록 저장", use_container_width=True):
            if c_last:
                found = False
                for cust in customers_db:
                    if cust["phone_last"] == c_last:
                        cust["visits"] += 1
                        cust["points"] += 1000
                        cust["memo"] = c_memo if c_memo else cust["memo"]
                        found = True
                        break
                if not found:
                    customers_db.append({"phone_last": c_last, "name": c_name if c_name else "고객", "visits": 1, "points": 1000, "memo": c_memo})
                save_customers(customers_db)
                st.success(f"{c_last} 고객님 적립 완료!")
                st.rerun()

# ==========================================
# 5. 메인 피드 섹션 4: PRO 마케팅 스튜디오 & AI 리뷰 답글기 (신규 기능 3)
# ==========================================
st.markdown("""
<div class="feed-card">
    <div class="feed-title">AI 마케팅 스튜디오 & 고객 소통 허브</div>
    <div class="feed-subtitle">블로그, 당근마켓, 인스타, CRM 문자 및 리뷰 자동 답글 솔루션</div>
</div>
""", unsafe_allow_html=True)

mkt_tab1, mkt_tab2, mkt_tab3, mkt_tab4, mkt_tab5 = st.tabs([
    "네이버 블로그", "당근마켓 소식", "인스타그램 피드", "단골 CRM 문자", "리뷰 자동 답글기"
])

with mkt_tab1:
    if not is_pro_user: st.info("블로그 SEO 알고리즘 원고는 PRO 회원 전용 기능입니다.")
    else:
        bl_kw = st.text_input("메인 공략 키워드", value=f"용인 {sel_industry.split('/')[0].strip()}", key="cp_bl_kw")
        bl_sub = st.text_input("서브 연관 검색어", value="처인구 안경, 송전리 안경점", key="cp_bl_sub")
        if st.button("블로그 최적화 원고 생성", key="cp_bl_btn", use_container_width=True):
            out = generate_safe_content(f"상호: {store_name}\n키워드: {bl_kw}, {bl_sub}\n강점: {sel_feature}\n네이버 플레이스 연동 블로그 원고 작성.")
            if out: st.text_area("작성된 원고", value=out, height=320)

with mkt_tab2:
    if not is_pro_user: st.info("당근마켓 동네생활 바이럴은 PRO 회원 전용 기능입니다.")
    else:
        dg_top = st.selectbox("소식 주제", ["첫 방문 혜택 안내", "신상품 입고", "단기 프로모션"], key="cp_dg_top")
        if st.button("당근마켓 소식글 생성", key="cp_dg_btn", use_container_width=True):
            out = generate_safe_content(f"상호: {store_name}\n업종: {sel_industry}\n주제: {dg_top}\n당근마켓 신뢰감 있는 동네생활 소식글 작성.")
            if out: st.text_area("당근 소식", value=out, height=280)

with mkt_tab3:
    if not is_pro_user: st.info("인스타그램 비주얼 피드는 PRO 회원 전용 기능입니다.")
    else:
        ig_fmt = st.selectbox("포맷", ["단일 피드", "카드뉴스형", "릴스 스크립트"], key="cp_ig_fmt")
        if st.button("인스타그램 피드 & 태그 생성", key="cp_ig_btn", use_container_width=True):
            out = generate_safe_content(f"상호: {store_name}\n포맷: {ig_fmt}\n강점: {sel_feature}\n인스타 피드 및 태그 15개 작성.")
            if out: st.text_area("인스타 피드", value=out, height=280)

with mkt_tab4:
    if not is_pro_user: st.info("고객 리텐션 CRM 메시지는 PRO 회원 전용 기능입니다.")
    else:
        crm_tgt = st.selectbox("발송 대상", ["첫 방문 후 재방문 유도", "60일 이상 미방문 고객", "정기 검안 점검 안내"], key="cp_crm_tgt")
        if st.button("SMS / LMS / 알림톡 3종 생성", key="cp_crm_btn", use_container_width=True):
            out = generate_safe_content(f"상호: {store_name}\n대상: {crm_tgt}\n혜택: {my_perk}\nSMS 및 LMS, 알림톡 3종 규격 작성.")
            if out: st.text_area("CRM 메시지", value=out, height=300)

with mkt_tab5:
    st.markdown("###### 💬 네이버 영수증 & 배민/당근 고객 리뷰 답글기")
    cust_review = st.text_area("고객이 남긴 리뷰 본문 붙여넣기", placeholder="예: 시력검사도 꼼꼼하게 해주시고 안경테도 잘 골라주셔서 너무 만족해요!")
    rev_tone = st.selectbox("답글 스타일", ["감사하고 따뜻한 정중형", "센스 있고 친근한 이웃형", "전문 지식이 돋보이는 프로형"], key="rev_tone_sel")
    if st.button("맞춤형 전문 답글 3종 생성", key="cp_rev_btn", use_container_width=True):
        if cust_review:
            out = generate_safe_content(f"상호: {store_name}\n고객리뷰: '{cust_review}'\n스타일: {rev_tone}\n네이버 영수증/플레이스 전용 감동적인 답글 3종 작성.")
            if out: st.text_area("추천 답글 3종", value=out, height=260)
        else:
            st.warning("고객 리뷰 본문을 입력해 주세요.")

# ==========================================
# 6. 메인 피드 섹션 5: 행정서류 & 2026 정책지원 분석
# ==========================================
st.markdown("""
<div class="feed-card">
    <div class="feed-title">정책자금 필수 행정 서식 & 2026 국비 지원 분석</div>
    <div class="feed-subtitle">소상공인확인서, 부가세증명 등 4대 서류 원스톱 및 맞춤형 정책 진단</div>
</div>
""", unsafe_allow_html=True)

gov_tab1, gov_tab2 = st.tabs(["4대 필수 서류 발급 가이드", "2026 정책금융 AI 진단"])

with gov_tab1:
    st.markdown("""
    | 서류명 | 주 발급처 | 신청 대상 및 용도 | 법정 수수료 | 평균 소요시간 |
    | :--- | :--- | :--- | :--- | :--- |
    | **소상공인확인서** | 중소기업현황정보시스템 | 정부 지원사업, 국비 지원금 신청 시 소상공인 증빙 | 무료 | 즉시 (온라인) |
    | **부가가치세 과세표준증명** | 국세청 홈택스 / 손택스 | 대출 심사, 보증 심사 시 사업장 매출 규모 증빙 | 무료 | 즉시 (온라인) |
    | **국세 완납증명서 (납세증명)** | 국세청 홈택스 | 세금 체납 여부 확인 (미납 시 정책 지원 전면 제한) | 무료 | 즉시 (온라인) |
    | **지방세 완납증명서** | 정부24 / 주민센터 | 지방세(재산세, 주민세 등) 체납 여부 확인 | 무료 | 즉시 (온라인) |
    """)
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.link_button("중소기업현황정보시스템 (소상공인확인서)", "https://sminfo.mss.go.kr", use_container_width=True)
        st.link_button("국세청 홈택스 (부가세/국세완납)", "https://www.hometax.go.kr", use_container_width=True)
    with col_g2:
        st.link_button("정부24 (지방세 완납증명)", "https://www.gov.kr", use_container_width=True)
        st.link_button("소상공인정책자금 포털", "https://ols.semas.or.kr", use_container_width=True)

with gov_tab2:
    st.markdown("""
    <div class="policy-grid">
        <div class="policy-box">
            <span style="font-size:0.75rem; font-weight:700; color:#2563EB;">비용 절감</span>
            <div style="font-weight:700; margin:4px 0;">전기요금 특별지원</div>
            <div style="font-size:0.85rem; color:#4B5563;">최대 20~25만 원 전기료 감면</div>
            <a href="https://www.소상공인전기요금특별지원.kr" target="_blank" style="text-decoration:none; margin-top:8px;">
                <button style="width:100%; height:32px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.8rem; font-weight:700; cursor:pointer;">신청처 바로가기</button>
            </a>
        </div>
        <div class="policy-box">
            <span style="font-size:0.75rem; font-weight:700; color:#2563EB;">금융 이자 경감</span>
            <div style="font-weight:700; margin:4px 0;">고금리 저금리 대환보증</div>
            <div style="font-size:0.85rem; color:#4B5563;">7% 이상 대출을 4%대로 전환</div>
            <a href="https://www.semas.or.kr" target="_blank" style="text-decoration:none; margin-top:8px;">
                <button style="width:100%; height:32px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.8rem; font-weight:700; cursor:pointer;">공고 확인하기</button>
            </a>
        </div>
        <div class="policy-box">
            <span style="font-size:0.75rem; font-weight:700; color:#2563EB;">매장 인프라</span>
            <div style="font-weight:700; margin:4px 0;">스마트상점 국비 지원</div>
            <div style="font-size:0.85rem; color:#4B5563;">키오스크/테이블오더 70% 보조</div>
            <a href="https://www.sbiz.or.kr/smst/index.do" target="_blank" style="text-decoration:none; margin-top:8px;">
                <button style="width:100%; height:32px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.8rem; font-weight:700; cursor:pointer;">공고 확인하기</button>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_pol1, col_pol2 = st.columns(2)
    with col_pol1:
        rev_scale = st.selectbox("사업장 연매출 규모", ["3천만 원 미만 (영세)", "3천만 원 ~ 1억 원", "1억 원 ~ 3억 원", "3억 원 초과"], key="cp_rev_scale")
    with col_pol2:
        aid_purp = st.selectbox("가장 시급한 지원", ["고금리 대출 이자 완화", "매장 설비/키오스크 보조", "운영 고정비 지원"], key="cp_aid_purp")
    if st.button("내 매장 맞춤 정책자금 AI 진단서 확인", key="cp_aid_btn", use_container_width=True):
        out = generate_safe_content(f"업종: {sel_industry}\n매출: {rev_scale}\n목적: {aid_purp}\n가장 유리한 정부 정책 2종과 신청 요건을 공문서 리포트로 작성.")
        if out: st.markdown(f"<div style='background:#F8FAFC; border-left:3px solid #2563EB; padding:14px; border-radius:8px;'>{out}</div>", unsafe_allow_html=True)

# ==========================================
# 7. 메인 피드 섹션 6: 알바 급여 계산 & 영업 마감 플래너
# ==========================================
st.markdown("""
<div class="feed-card">
    <div class="feed-title">경영 지원: 파트타이머 급여 & 일일 결산 플래너</div>
    <div class="feed-subtitle">주휴수당 자동 계산 및 당일 운영 분석·내일 실행 과제 리포트</div>
</div>
""", unsafe_allow_html=True)

fin_tab1, fin_tab2, fin_tab3 = st.tabs(["알바 급여 계산기", "일일 영업 결산 리포트", "매장 시간대별 음악"])

with fin_tab1:
    w1, w2 = st.columns(2)
    with w1:
        wage = st.number_input("시급 (원)", value=10030, step=100, key="feed_wage")
        hrs = st.number_input("주당 소정근로시간", value=16.0, step=0.5, key="feed_hrs")
    with w2:
        tax_opt = st.selectbox("공제 방식", ["사업소득세 3.3% 공제", "고용보험 0.9% 공제", "공제 없음"], key="feed_tax")
    base = wage * hrs * 4.345
    holiday = ((hrs / 40.0) * 8.0 * wage * 4.345) if hrs >= 15 else 0
    tot = base + holiday
    ded = tot * 0.033 if "3.3%" in tax_opt else (tot * 0.009 if "0.9%" in tax_opt else 0)
    net = tot - ded
    st.markdown(f"""
    <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:14px; margin-top:8px;">
        <div style="font-size:0.85rem; color:#6B7280;">기본급 {int(base):,}원 + 주휴수당 {int(holiday):,}원 (공제 {int(ded):,}원)</div>
        <div style="font-size:1.25rem; font-weight:800; color:#111827; margin-top:2px;">예상 실수령액: {int(net):,}원</div>
    </div>
    """, unsafe_allow_html=True)

with fin_tab2:
    cl_col1, cl_col2 = st.columns(2)
    with cl_col1:
        c_sales = st.text_input("오늘 매출액 (선택)", placeholder="예: 850,000원", key="feed_close_sales")
        c_flow = st.selectbox("고객 유입 체감", ["평소 대비 한산함", "평균 수준", "피크타임 집중 방문", "종일 만석"], key="feed_close_flow")
    with cl_col2:
        c_memo = st.text_input("특이사항/이슈", placeholder="예: 특정 제품 품절", key="feed_close_memo")
        c_sat = st.selectbox("운영 만족도", ["다소 아쉬움", "무난하고 안정적", "매우 만족"], key="feed_close_sat")
    if st.button("일일 영업 결산 & 내일 액션플랜 생성", key="feed_close_btn", use_container_width=True):
        out = generate_safe_content(f"가게: {store_name}\n매출: {c_sales}\n유입: {c_flow}\n특이사항: {c_memo}\n만족도: {c_sat}\n일일 경영 총평, 내일 실행과제 3가지, 퇴근길 멘탈 리셋 한마디 작성.")
        if out: st.markdown(f"<div style='background:#F8FAFC; border-left:3px solid #2563EB; padding:14px; border-radius:8px;'>{out}</div>", unsafe_allow_html=True)

with fin_tab3:
    m_time = st.selectbox("시간대", ["오전 오픈", "점심/오후 피크", "나른한 오후 3~5시", "저녁 골든타임", "마감 정리"], key="feed_m_time")
    m_style = st.selectbox("장르", ["재즈/보사노바", "어쿠스틱 팝", "2000년대 감성 발라드 피아노", "9000 댄스"], key="feed_m_style")
    yt_q = f"{m_style.split('/')[0]} {m_time} 플레이리스트 연속재생"
    st.link_button(f"유튜브 '{yt_q}' 스트리밍 재생", f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_q)}", use_container_width=True)
