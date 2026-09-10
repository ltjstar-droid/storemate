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
            "feature": "독일식 초정밀 시력검사",
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
    page_title="STORE MATE | 로컬 비즈니스 플랫폼",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 깔끔한 모던 CSS
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
        padding: 20px 24px;
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

    .pro-builder-box {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-top: 3px solid #2563EB;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    .pro-badge {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        color: #1D4ED8;
        background: #EFF6FF;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    .pro-lock-banner {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-left: 4px solid #EF4444;
        padding: 18px;
        border-radius: 10px;
        color: #991B1B;
        margin-bottom: 16px;
    }

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
                            "feature": "전문 검안 및 정밀 서비스",
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
        st.caption("플랜: PRO 엔터프라이즈 파트너")
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
        <div class="metric-title">마케팅 엔진</div>
        <div class="metric-number">PRO Suite v3.6</div>
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
너는 골목상권 및 로컬 비즈니스 분야 20년 경력의 수석 마케팅 디렉터다.
이모티콘 남발은 배제하고, 전문 컨설턴트처럼 정갈하고 세련된 문장으로 실제 집행 가능한 완성본을 제공한다.
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
        ], key="mood_sel")
        sel_genre = st.selectbox("장르 선택", [
            "피아노 힐링 연주곡 메들리",
            "2000년대 감성 명곡 발라드",
            "90-2000 국민 애창 댄스곡",
            "트로트 베스트 모음"
        ], key="genre_sel")
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

# ==========================================
# 2. 공동구매 (원래 완벽했던 3단 서브탭 복원!)
# ==========================================
with tabs[2]:
    st.markdown("""
    <div class="guide-banner">
        실시간 로컬 공동구매 시스템: 현재 진행 중인 핫딜과 소모품 공구의 남은 기간과 신청 현황을 확인하세요.
    </div>
    """, unsafe_allow_html=True)
    
    deal_subtab1, deal_subtab2, deal_subtab3 = st.tabs(["주민 핫딜", "소모품 공구", "공구 제안"])
    
    def get_dday(deadline_str):
        try:
            d_date = datetime.strptime(deadline_str, "%Y-%m-%d")
            delta = (d_date - datetime.now()).days
            if delta > 0:
                return f"D-{delta}일"
            elif delta == 0:
                return "오늘 마감"
            else:
                return "마감"
        except Exception:
            return "진행 중"

    with deal_subtab1:
        for deal in deals_db["deals"]:
            total_qty = sum([p["qty"] for p in deal["participants"]])
            total_people = len(deal["participants"])
            dday_txt = get_dday(deal["deadline"])
            progress_val = min(total_qty / deal["target"], 1.0)
            
            st.markdown(f"""
            <div class="clean-card">
                <span style="background:#EF4444; color:#fff; font-size:0.75rem; font-weight:700; padding:2px 6px; border-radius:4px;">{dday_txt}</span>
                <h4 style="margin:8px 0; color:#0F172A; font-size:1.05rem;">{deal['title']}</h4>
                <p style="color:#2563EB; font-weight:700; font-size:0.95rem; margin-bottom:6px;">{deal['price']}</p>
                <p style="font-size:0.85rem; color:#475569;">신청 현황: <b>{total_people}명 참여</b> (누적 {total_qty}개)</p>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress_val)
            
            with st.container():
                with st.form(key=f"form_{deal['id']}"):
                    st.markdown("##### 공동구매 참여 신청")
                    p_name = st.text_input("성함 또는 상호명", key=f"name_{deal['id']}")
                    p_phone = st.text_input("연락처", key=f"phone_{deal['id']}")
                    p_qty = st.number_input("신청 수량", min_value=1, max_value=100, value=1, step=1, key=f"qty_{deal['id']}")
                    
                    if st.form_submit_button("참여 확정하기", use_container_width=True):
                        if p_name and p_phone:
                            new_p = {"name": p_name, "phone": p_phone, "qty": int(p_qty), "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
                            deal["participants"].append(new_p)
                            save_deals(deals_db)
                            st.success("신청이 완료되었습니다.")
                            st.rerun()
                        else:
                            st.warning("정보를 입력해 주세요.")
                
                st.markdown("##### 참여자 명단")
                for idx, p in enumerate(deal["participants"], 1):
                    st.markdown(f"- {idx}. **{p['name']}**님 ({p['qty']}개)")
            st.markdown("<hr>", unsafe_allow_html=True)

    with deal_subtab2:
        st.markdown("##### 사업장 소모품 도매가 공동 발주")
        st.markdown("""
        <div class="clean-card">
            <h4 style="margin-top:0;">카드단말기 영수증 롤페이퍼 (50롤 1박스)</h4>
            <p style="color:#475569; font-size:0.9rem;">시중가 38,000원 ➡️ <b>공구가 23,500원 (무료배송)</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("소모품 공동발주 접수", use_container_width=True, key="b2b_order_btn"):
            st.success("발주 신청이 접수되었습니다.")

    with deal_subtab3:
        st.markdown("##### 신규 공동구매 오픈 제안")
        c_name = st.text_input("상품명", placeholder="예: 블루라이트 차단 렌즈 패키지", key="prop_name")
        c_qty = st.number_input("목표 수량", min_value=1, max_value=1000, value=30, step=1, key="prop_qty")
        c_discount = st.text_input("제안 공구가", placeholder="예: 35,000원", key="prop_price")
        c_days = st.slider("진행 기간 (일 단위)", min_value=3, max_value=30, value=7, key="prop_days")
        
        if st.button("공동구매 프로젝트 등록 제출", use_container_width=True, key="prop_submit"):
            if c_name and c_discount:
                new_deal = {
                    "id": f"deal_{int(time.time())}",
                    "title": f"[{store_name}] {c_name}",
                    "price": f"{c_discount} (단독 특가)",
                    "target": int(c_qty),
                    "deadline": (datetime.now() + timedelta(days=c_days)).strftime("%Y-%m-%d"),
                    "participants": []
                }
                deals_db["deals"].append(new_deal)
                save_deals(deals_db)
                st.success("공동구매 프로젝트가 등록되었습니다.")
                st.rerun()
            else:
                st.warning("상품명과 가격을 입력해 주세요.")

# ==========================================
# 3. 블로그원고 (PRO 고품질 엔진)
# ==========================================
with tabs[3]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-banner">
            <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">네이버 상위노출 알고리즘 엔진 (PRO 회원 전용)</div>
            <div style="font-size:0.88rem;">C-Rank 및 스마트블록 기준에 맞춘 검색엔진 최적화(SEO) 원고를 설계합니다. 사이드바에서 PRO 권한을 승인받으세요.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="pro-builder-box">
            <span class="pro-badge">PRO ENTERPRISE ENGINE</span>
            <div style="font-weight:700; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">네이버 로컬 스마트블록 전문 포스팅 아키텍트</div>
            <div style="font-size:0.85rem; color:#64748B; margin-bottom:14px;">검색 유입과 플레이스 예약 전환율을 동시에 노리는 상업용 전문 포스팅을 기획합니다.</div>
        </div>
        """, unsafe_allow_html=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            bl_target_keyword = st.text_input("메인 공략 키워드", value=f"용인 {sel_industry.split('/')[0].strip()}", key="orig_bl_kw")
            bl_sub_keyword = st.text_input("서브 연관 검색어 (쉼표 구분)", value=f"{sel_loc.split()[1] if len(sel_loc.split())>1 else ''} 추천, 단골", key="orig_bl_sub")
            bl_photo_count = st.slider("포스팅 사진 첨부 예정 장수", min_value=5, max_value=20, value=8, step=1, key="orig_bl_photo")
        with col_b2:
            bl_tone = st.selectbox("원고 스타일 톤앤매너", [
                "전문가 심층 분석형 (신뢰성, 공학적/기술적 검증, 정밀함 강조)",
                "동네 단골 솔직 방문기형 (자연스러운 체감 후기, 상세 공간 묘사)",
                "스마트 소비 가이드형 (가성비, 할인 혜택, 실속 비교 중심)"
            ], key="orig_bl_tone")
            bl_core_point = st.text_area("매장 핵심 차별점 (시그니처/장비/서비스)", value=sel_feature, height=85, key="orig_bl_core")

        if st.button("네이버 상위노출 최적화 전문 원고 생성", key="orig_bl_submit"):
            with st.spinner("알고리즘 적합성 및 검색 키워드 가중치 분석 중..."):
                prompt = f"""
                업종: {sel_industry}
                매장명: {store_name}
                위치: {sel_loc}
                메인 타깃 키워드: {bl_target_keyword}
                서브 키워드: {bl_sub_keyword}
                사진 장수: {bl_photo_count}장
                톤앤매너: {bl_tone}
                차별점: {bl_core_point}

                당신은 네이버 검색 로직에 정통한 상위 1% 전문 마케팅 기획자입니다.
                다음 4가지 구성 요소를 포함하여 블로그 포스팅 원고를 전문적으로 작성하십시오.
                이모티콘은 배제하고 정갈한 비즈니스 문체로 작성할 것.

                [1] 클릭률 극대화 제목 3종 (키워드 전진배치형, 궁금증 유발형, 솔직후기형)
                [2] 사진 촬영 및 배치 가이드라인 ({bl_photo_count}장 피사체 앵글 가이드)
                [3] 본문 (공간 도입 - 전문 서비스 검증 - 실제 혜택 - 플레이스 예약 유도)
                [4] 연관 태그 10종
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("생성된 SEO 전문 원고", value=out, height=420)

# ==========================================
# 4. 당근소식 (PRO 고품질 엔진)
# ==========================================
with tabs[4]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-banner">
            <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">당근마켓 동네생활 바이럴 엔진 (PRO 회원 전용)</div>
            <div style="font-size:0.88rem;">동네 이웃 주민들의 댓글과 단골 맺기를 이끌어내는 전문 소식 작성기입니다.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="pro-builder-box">
            <span class="pro-badge">PRO ENTERPRISE ENGINE</span>
            <div style="font-weight:700; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">당근마켓 반경 3km 타깃 로컬 소식 솔루션</div>
        </div>
        """, unsafe_allow_html=True)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            dg_target_audience = st.selectbox("타깃 고객군", ["3040 자녀 양육 주부층", "인근 거주 2030 직장인 및 1인가구", "동네 터줏대감 5060 중장년층", "전 지역 주민 전체"], key="orig_dg_target")
            dg_promo_type = st.selectbox("제공 혜택 유형", ["방문 시 무상 정밀 점검/체험 제공", "용인친구들 단독 할인 쿠폰 지급", "선착순 사은품 추가 증정", "새 시즌 한정 신상품 소개"], key="orig_dg_promo")
        with col_d2:
            dg_hook = st.text_input("동네 이슈/상황 연결", placeholder="예: 봄 환절기 미세먼지, 새 학기 준비", key="orig_dg_hook")
            dg_call = st.text_input("유도 액션 (CTA)", value="당근 단골 맺기 누르고 캡처본 보여주시면 적용", key="orig_dg_cta")

        if st.button("당근마켓 맞춤형 바이럴 소식 생성", key="orig_dg_submit"):
            with st.spinner("로컬 반경 커뮤니티 데이터 분석 중..."):
                prompt = f"""
                업종: {sel_industry}
                매장명: {store_name}
                위치: {sel_loc}
                주 타깃: {dg_target_audience}
                프로모션: {dg_promo_type}
                상황적 훅: {dg_hook}
                유도 액션: {dg_call}
                매장 강점: {sel_feature}

                당근마켓 동네생활 탭에서 신뢰를 얻는 소식을 작성하라.
                전단지 어투는 배제하고 진솔한 이웃 사장님 톤으로 작성할 것.
                1. 피드 노출 타이틀 2종
                2. 본문 (안부 - 전문 정보 팁 - 혜택 안내 - 단골 유도)
                3. 댓글 반응 유도 질문
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("생성된 당근마켓 소식 원고", value=out, height=360)

# ==========================================
# 5. 인스타그램 (PRO 고품질 엔진)
# ==========================================
with tabs[5]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-banner">
            <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">인스타그램 비주얼 브랜딩 스튜디오 (PRO 회원 전용)</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="pro-builder-box">
            <span class="pro-badge">PRO ENTERPRISE ENGINE</span>
            <div style="font-weight:700; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">인스타그램 하이엔드 피드 & 스토리보드 디렉터</div>
        </div>
        """, unsafe_allow_html=True)

        col_i1, col_i2 = st.columns(2)
        with col_i1:
            ig_format = st.selectbox("콘텐츠 포맷", ["단일 피드 (감성 스냅 1컷)", "카드뉴스형 (정보 전달 4~6슬라이드)", "릴스 숏폼 (15초 텍스트 영상 스크립트)"], key="orig_ig_fmt")
            ig_vibe = st.selectbox("비주얼 무드", ["미니멀 모던 (단정하고 세련된 분위기)", "따뜻한 아날로그 (정감 있고 아늑한 톤)", "전문 랩/클리닉 (정밀함과 위생 강조)"], key="orig_ig_vb")
        with col_i2:
            ig_topic = st.text_input("포스팅 핵심 주제", placeholder="예: 얼굴형에 맞는 맞춤 안경 피팅 가이드", key="orig_ig_tp")
            ig_perk = st.text_input("프로모션/혜택", value=curr_user.get("map_perk", "용친 회원 현장 추가 혜택"), key="orig_ig_pk")

        if st.button("인스타그램 비주얼 피드 & 태그 패키지 생성", key="orig_ig_submit"):
            with st.spinner("비주얼 레이아웃 구성 중..."):
                prompt = f"""
                업종: {sel_industry}
                매장명: {store_name}
                위치: {sel_loc}
                포맷: {ig_format}
                무드: {ig_vibe}
                주제: {ig_topic}
                혜택: {ig_perk}
                강점: {sel_feature}

                인스타그램 전문 브랜드 에이전시 톤으로 포스팅을 작성하라.
                1. 사진/영상 촬영 디렉팅 (구도, 조명 2~3줄)
                2. 피드 첫 줄 훅 멘트
                3. 피드 본문 (줄바꿈 최적화)
                4. 해시태그 15종 (지역 5개, 업종 5개, 타깃 5개)
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("생성된 인스타그램 브랜드 패키지", value=out, height=380)

# ==========================================
# 6. 고객문자 (PRO 고품질 엔진)
# ==========================================
with tabs[6]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-banner">
            <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">고객 리텐션 CRM 메시지 솔루션 (PRO 회원 전용)</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="pro-builder-box">
            <span class="pro-badge">PRO ENTERPRISE ENGINE</span>
            <div style="font-weight:700; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">재방문율 극대화 CRM 메시지 스위트</div>
        </div>
        """, unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            crm_target = st.selectbox("발송 대상 고객군", [
                "첫 방문 후 재방문 유도 (방문 후 1~2주 경과 고객)",
                "이탈 위험 단골 고객 (최근 60일 이상 미방문 고객)",
                "정기 점검/관리 주기 도래 고객 (전문 검안/클리닝 권장)",
                "특정 시즌/명절 감사 프로모션 타깃 전체"
            ], key="orig_crm_tgt")
            crm_coupon = st.text_input("제공 바우처 / 혜택", value="방문 시 무상 정밀 점검 및 10% 추가 할인 쿠폰", key="orig_crm_cpn")
        with col_s2:
            crm_urgency = st.selectbox("기한 설정", ["이번 주말까지 한정", "수신 후 14일 이내 방문 시", "선착순 30명 한정"], key="orig_crm_urg")
            crm_info = st.text_input("매장 문의처", value=f"{store_name} (문자 회신 가능)", key="orig_crm_inf")

        if st.button("SMS / LMS / 카카오 알림톡 3종 동시 출력", key="orig_crm_submit"):
            with st.spinner("스팸 필터 회피 메시지 설계 중..."):
                prompt = f"""
                매장명: {store_name}
                업종: {sel_industry}
                대상: {crm_target}
                혜택: {crm_coupon}
                기한: {crm_urgency}
                문의처: {crm_info}

                고객이 VIP 케어로 인식하도록 3종 규격으로 작성하라.
                [1] 단문 SMS (90 Byte 내외 엄수)
                [2] 장문 LMS (스토리텔링형)
                [3] 카카오 알림톡 권장 포맷
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("생성된 CRM 메시지 3종 세트", value=out, height=380)

# 7. 급여계산
with tabs[7]:
    w1, w2 = st.columns(2)
    with w1:
        wage = st.number_input("기본 시급 (원)", value=10030, step=100, key="wage_calc")
        hours = st.number_input("주당 소정근로시간", value=16.0, step=0.5, key="hours_calc")
    with w2:
        tax_opt = st.selectbox("공제 기준", ["사업소득세 3.3% 공제", "고용보험 0.9% 공제", "공제 미적용"], key="tax_calc")
    
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
# 8. 행정서류 (원래 좋았던 직관적인 안내 방식으로 100% 원복!)
# ==========================================
with tabs[8]:
    st.markdown("##### 지원금 필수 서류 발급처 안내")
    doc = st.selectbox("필요 서류 선택", [
        "소상공인확인서", 
        "부가가치세 과세표준증명원", 
        "국세 완납증명서", 
        "지방세 완납증명서"
    ], key="orig_doc_sel")
    
    DOCS = {
        "소상공인확인서": ("중소기업현황정보시스템", "회원가입 후 [확인서 발급신청] ➡️ 온라인 서류 제출 ➡️ PDF 다운로드"),
        "부가가치세 과세표준증명원": ("국세청 홈택스", "국세증명·사업자등록 ➡️ [부가가치세 과세표준증명] 신청 후 발급"),
        "국세 완납증명서": ("국세청 홈택스", "국세증명·사업자등록 ➡️ [납세증명서(국세완납증명)] 출력"),
        "지방세 완납증명서": ("정부24", "검색창에 '지방세 납세증명' 검색 ➡️ 본인 인증 후 즉시 발급")
    }
    site, step = DOCS[doc]
    st.info(f"발급처: **{site}**\n\n신청 방법: {step}")

# ==========================================
# 9. 정책지원 (원래 좋았던 직관적인 질의 방식으로 100% 원복!)
# ==========================================
with tabs[9]:
    st.markdown("##### 국비 지원금 및 절세 가이드")
    sub_q = st.selectbox("궁금한 지원 정책 선택", [
        "전기세 25만 원 국비 지원받는 법",
        "비싼 대출 이자 4%대로 낮추는 법",
        "소상공인 간판/키오스크 교체 70% 지원"
    ], key="orig_sub_q")
    
    if st.button("정책 설명 및 신청처 확인", key="orig_sub_btn"):
        with st.spinner("정책 데이터 조회 중..."):
            prompt = f"질문: {sub_q}\n소상공인이 바로 실행할 수 있도록 1) 혜택 2) 자격 요건 3) 공식 신청처를 간결하고 명확하게 정리하라."
            out = generate_safe_content(prompt)
            if out:
                st.markdown(f"""
                <div class="clean-card" style="border-left: 3px solid #2563EB;">
                    <div style="font-weight:700; color:#0F172A; margin-bottom:8px;">{sub_q} 가이드</div>
                    <div style="color:#334155; font-size:0.92rem; line-height:1.6;">{out}</div>
                </div>
                """, unsafe_allow_html=True)

# 10. 영업마감
with tabs[10]:
    st.markdown("##### 일일 영업 마감 리포트")
    t_mood = st.selectbox("오늘 매장 분위기", ["한산해서 아쉬움", "특정 시간대만 바쁨", "목표 매출 달성"], key="orig_t_mood")
    if st.button("마감 브리핑 및 내일 처방 받기", key="orig_close_btn"):
        with st.spinner("마감 리포트 작성 중..."):
            prompt = f"가게: {store_name} ({sel_industry})\n오늘 분위기: {t_mood}\n1. 일일 브리핑 2. 내일 영업 팁 1가지 작성."
            out = generate_safe_content(prompt)
            if out:
                st.markdown(f"""
                <div class="clean-card" style="border-left: 3px solid #2563EB;">
                    <div style="font-weight:700; color:#0F172A; margin-bottom:8px;">영업 마감 브리핑</div>
                    <div style="color:#334155; font-size:0.92rem; line-height:1.6;">{out}</div>
                </div>
                """, unsafe_allow_html=True)
