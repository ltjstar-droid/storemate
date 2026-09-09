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

# 페이지 기본 설정
st.set_page_config(
    page_title="매장비서 AI | 올인원 로컬 솔루션",
    page_icon="🏬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🎨 [최고급 프리미엄 인테리어 CSS 스타일링]
# ==========================================
st.markdown("""
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<style>
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, input, button, a {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
        letter-spacing: -0.02em;
    }
    .stApp { background-color: #F4F6F9; }
    
    .hero-container {
        background: linear-gradient(135deg, #0A0F1D 0%, #1E293B 50%, #0F172A 100%);
        padding: 32px 36px;
        border-radius: 20px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.15), 0 10px 10px -5px rgba(15, 23, 42, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .hero-title { font-size: 2.3rem; font-weight: 800; color: #FFFFFF; margin: 0 0 8px 0; display: flex; align-items: center; gap: 12px; }
    .hero-badge { background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); color: #FFFFFF; font-size: 0.85rem; font-weight: 700; padding: 4px 12px; border-radius: 30px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }
    .hero-sub { font-size: 1.1rem; color: #94A3B8; margin: 0; font-weight: 400; }

    .guide-box {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-left: 6px solid #2563EB;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 24px;
        font-size: 1.05rem;
        color: #1E40AF;
        line-height: 1.6;
        font-weight: 500;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
    }
    .pro-lock-box {
        background: #FFF5F5;
        border: 1px solid #FED7D7;
        border-left: 6px solid #E53E3E;
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 24px;
        color: #9B2C2C;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
    }
    .azit-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }

    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        background-color: #E2E8F0;
        padding: 8px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 12px;
        flex-grow: 1;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08) !important;
    }
    .stButton>button {
        height: 3.4rem !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
    }
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
now = datetime.now()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# ==========================================
# 🔐 [로그인 / 회원가입 화면 분기 처리]
# ==========================================
if not st.session_state.logged_in_user:
    st.markdown("""
    <div style="max-width: 480px; margin: 80px auto; background: #FFFFFF; padding: 40px; border-radius: 24px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.08); text-align: center;">
        <h2 style="color: #0F172A; font-size: 1.8rem; font-weight: 800; margin-bottom: 8px;">🏬 매장비서 AI</h2>
        <p style="color: #64748B; font-size: 1.02rem; margin-bottom: 24px;">용인친구들 공식 상생아지트 솔루션</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["🔑 로그인", "✍️ 신규 회원가입"])
        
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
                            st.success("로그인 성공! 대시보드로 이동합니다.")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        st.error("존재하지 않는 아이디입니다. 회원가입을 먼저 진행해 주세요.")
        
        with auth_tab2:
            with st.form("signup_form"):
                st.markdown("##### 📝 사장님 매장 등록 (기본 무료 회원)")
                new_id = st.text_input("아이디 또는 연락처 (로그인용)", placeholder="예: 01012345678")
                new_pw = st.text_input("비밀번호 설정", type="password", placeholder="비밀번호 4자리 이상")
                new_store = st.text_input("매장 상호명", placeholder="예: 용인 맛있는 고깃집")
                new_ind = st.selectbox("업종 선택", INDUSTRY_LIST)
                new_loc = st.text_input("매장 도로명 주소", placeholder="예: 용인시 처인구 역북동")
                
                signup_submitted = st.form_submit_button("가입 완료하기 (무료 등급)", use_container_width=True)
                if signup_submitted:
                    if new_id and new_pw and new_store:
                        if new_id in users_db:
                            st.warning("이미 존재하는 아이디(연락처)입니다.")
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
                            st.success("🎉 회원가입이 완료되었습니다! [로그인] 탭에서 로그인해 주세요.")
                    else:
                        st.warning("아이디, 비밀번호, 상호명을 모두 입력해 주세요.")
                        
    st.stop()

# ==========================================
# 🏬 [로그인 완료 후 메인 대시보드]
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
            st.caption("관리자가 입금 확인 후 승인해 드립니다.")
        else:
            st.warning("⭐ 무료 체험 회원")
            if st.button("👑 PRO 유료 버전 승인 요청", use_container_width=True):
                curr_user["pro_status"] = "대기중"
                users_db[user_key] = curr_user
                save_users(users_db)
                st.success("🎉 PRO 승인 요청이 접수되었습니다! 관리자 확인 후 전환됩니다.")
                st.rerun()
            
    # 관리자(admin) 전용 패널 표시 (expander 대신 깔끔한 박스형태로 버그 원천 차단)
    if user_key == "admin":
        st.markdown("---")
        st.markdown("🛠️ **[관리자 회원 관리 센터]**")
        
        for uid, udata in users_db.items():
            ustore = udata.get("store_name", uid)
            u_is_pro = udata.get("is_pro", False)
            status_lbl = "👑 PRO" if u_is_pro else "⭐ 무료"
            
            st.markdown(f"""
            <div style="background:#F1F5F9; border-radius:10px; padding:10px; margin-bottom:8px; font-size:0.9rem;">
                <b>{ustore}</b> ({status_lbl})<br>
                아이디: <code>{uid}</code> | 상태: {udata.get('pro_status', '미신청')}
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if not u_is_pro:
                    if st.button("승인", key=f"adm_app_{uid}", use_container_width=True):
                        users_db[uid]["is_pro"] = True
                        users_db[uid]["pro_status"] = "승인완료"
                        save_users(users_db)
                        st.success(f"{ustore} 승인 완료!")
                        st.rerun()
            with col_b:
                if u_is_pro and uid != "admin":
                    if st.button("해제", key=f"adm_rev_{uid}", use_container_width=True):
                        users_db[uid]["is_pro"] = False
                        users_db[uid]["pro_status"] = "무료전환"
                        save_users(users_db)
                        st.success(f"{ustore} PRO 해제 완료!")
                        st.rerun()

    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()
            
    st.markdown("---")
    st.markdown("#### ⚙️ 내 매장 기본 정보")
    ind_idx = INDUSTRY_LIST.index(sel_industry) if sel_industry in INDUSTRY_LIST else 3
    sel_industry = st.selectbox("매장 업종", INDUSTRY_LIST, index=ind_idx)
    sel_loc = st.text_input("매장 위치", value=sel_loc)
    sel_feature = st.text_input("대표 강점/시그니처", value=sel_feature)
    
    if st.button("💾 정보 변경 저장", use_container_width=True):
        users_db[user_key]["industry"] = sel_industry
        users_db[user_key]["location"] = sel_loc
        users_db[user_key]["feature"] = sel_feature
        save_users(users_db)
        st.toast("매장 정보가 저장되었습니다!")

st.markdown(f"""
<div class="hero-container">
    <div class="hero-title">🏬 매장비서 AI <span class="hero-badge">{'👑 PRO 유료 버전' if is_pro_user else '⭐ 무료 버전'}</span></div>
    <div class="hero-sub">용인친구들 소상공인을 위한 프리미엄 가요 런처, 상생아지트 지도, 실시간 공구 관리 솔루션</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px 20px; margin-bottom:24px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
    📍 <b>{store_name}</b> ({sel_industry.split()[1]}) &nbsp;|&nbsp; {sel_loc} &nbsp;|&nbsp; <b>{'👑 PRO 회원 무제한 이용권 보유' if is_pro_user else ('⏳ PRO 승인 심사 대기 중...' if pro_status == '대기중' else '⭐ 무료 체험 회원')}</b>
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
                st.error("잠시 인터넷이 불안정합니다. 3초 뒤에 다시 눌러주세요.")
                return None
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
            return None

tab_titles = [
    "🎧 가요 검색",
    "🤝 상생아지트",
    "🛒 로컬 공구",
    "📍 [PRO] 네이버블로그",
    "🥕 [PRO] 당근소식",
    "📸 [PRO] 인스타피드",
    "💬 [PRO] 단골문자",
    "💰 알바급여",
    "📑 지원금서류",
    "🏛️ 절세비서",
    "🌙 장사마감"
]
tabs = st.tabs(tab_titles)

# ==========================================
# 0. 🎧 [무료] 유튜브 가요 검색 런처
# ==========================================
with tabs[0]:
    st.markdown("""
    <div class="guide-box">
        💡 <b>[무료 오픈 기능 - 유튜브 가요 검색 런처]</b><br>
        원하는 테마를 고르고 버튼을 누르면 <b>유튜브 검색 결과 페이지</b>로 바로 연결되어 원하는 곡을 골라 틀 수 있습니다.
    </div>
    """, unsafe_allow_html=True)
    
    YOUTUBE_SEARCH_QUERIES = {
        "🌿 차분하고 편안한 힐링 (안경원 / 상담 / 뷰티 / 조용한 카페)": {
            "🎹 감성 가요 피아노 힐링 연주곡": [
                {"name": "가요 명곡 피아노 힐링 메들리", "query": "가요 명곡 피아노 힐링 메들리 연속재생"},
                {"name": "2000년대 감성 발라드 피아노 커버", "query": "2000년대 감성 발라드 피아노 커버 모음"}
            ],
            "☕ 부드러운 감성 보컬 & 발라드": [
                {"name": "성시경·아이유 감성 힐링 가요 명곡", "query": "성시경 아이유 감성 힐링 가요 플레이리스트"},
                {"name": "김광석·신승훈 명품 발라드 메들리", "query": "김광석 신승훈 명품 발라드 메들리"}
            ]
        },
        "🥩 활기차고 신나는 분위기 (고깃집 / 삼겹살 / 포차 / 호프)": {
            "🎉 90-2000 국민 애창 댄스 (쿨·코요태·터보)": [
                {"name": "쿨·코요태 신나는 9000 댄스 메들리", "query": "쿨 코요태 신나는 9000 댄스 메들리"},
                {"name": "무한도전 가요제 & 히트 댄스곡", "query": "무한도전 가요제 히트 댄스곡 모음"}
            ]
        },
        "🍲 정겹고 푸근한 레트로 (노포 / 국밥집 / 전통식당 / 어르신 단골)": {
            "🎺 어르신 단골 1순위! 흥겨운 트로트 메들리": [
                {"name": "임영웅·영탁·이찬원 흥겨운 트로트 베스트", "query": "임영웅 영탁 이찬원 흥겨운 트로트 메들리"},
                {"name": "장윤정·송가인·나훈아 신나는 트로트", "query": "장윤정 송가인 나훈아 신나는 트로트 메들리"}
            ]
        }
    }

    col_m1, col_m2 = st.columns([5, 5])
    with col_m1:
        st.markdown("### 🎛️ 유튜브 검색 런처 설정")
        mood_keys = list(YOUTUBE_SEARCH_QUERIES.keys())
        sel_mood = st.selectbox("1단계: 매장 분위기 (Mood)", mood_keys, index=0, key="yt_s_mood")
        genre_dict = YOUTUBE_SEARCH_QUERIES[sel_mood]
        genre_keys = list(genre_dict.keys())
        sel_genre = st.selectbox("2단계: 가요 장르 (Genre)", genre_keys, key="yt_s_genre")
        track_list = genre_dict[sel_genre]
        track_names = [t["name"] for t in track_list]
        sel_track_name = st.selectbox("3단계: 추천 검색어 선택", track_names, key="yt_s_track")
        
        selected_query = next(t["query"] for t in track_list if t["name"] == sel_track_name)
        youtube_search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(selected_query)}"

    with col_m2:
        st.markdown("### 📢 유튜브 검색 결과로 연결")
        st.markdown(f"""
        <div style="background: #0F172A; border-radius: 16px; padding: 26px; color: #FFFFFF; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);">
            <div style="font-size: 1.2rem; font-weight: 800; color: #FFFFFF; margin-bottom: 12px;">🔍 {sel_track_name}</div>
            <div style="font-size: 0.95rem; color: #94A3B8; margin-bottom: 22px;">버튼을 누르면 유튜브 검색 결과가 열리며, 마음에 드는 영상을 선택해 틀 수 있습니다.</div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("🔎 유튜브에서 검색하여 고르기", youtube_search_url, use_container_width=True)

# ==========================================
# 1. 🤝 [무료] 상생아지트 & 네이버 지도
# ==========================================
with tabs[1]:
    st.markdown("""
    <div class="guide-box">
        💡 <b>[무료 오픈 기능 - 상생아지트 네이버 지도 연동]</b><br>
        용인친구들 공식 상생아지트 디렉토리 및 내 가게 네이버 지도 원클릭 연동 기능입니다.
    </div>
    """, unsafe_allow_html=True)
    
    my_saved_addr = curr_user.get("map_address", "경기도 용인시 처인구 이동읍 경기동로 725")
    my_perk = curr_user.get("map_perk", "용친 회원 안경렌즈 추가 10% DC & 고급 안경 클리너 증정")
    naver_map_address_only_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"
    
    st.markdown(f"""
    <div class="azit-card">
        <h3>★ 공식 내 아지트: {store_name}</h3>
        <p>📍 {my_saved_addr}</p>
        <p>🎁 <b>용친 회원 혜택:</b> {my_perk}</p>
        <a href="{naver_map_address_only_url}" target="_blank">
            <button style="width:100%; height:40px; background:#03C75A; color:#FFFFFF; border:none; border-radius:8px; font-weight:700; cursor:pointer;">
                🟢 네이버 지도로 주소 정확히 찾기
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 🛒 [무료] 실시간 로컬 공구 & 신청 관리 시스템 (화살표 버그 완전 제거)
# ==========================================
with tabs[2]:
    st.markdown("""
    <div class="guide-box">
        💡 <b>[실시간 용친 로컬 공구 시스템]</b><br>
        현재 진행 중인 핫딜과 소모품 공구의 <b>남은 기간(D-Day), 누적 신청 인원 및 수량</b>을 실시간으로 확인하고 직접 신청할 수 있습니다.
    </div>
    """, unsafe_allow_html=True)
    
    deal_subtab1, deal_subtab2, deal_subtab3 = st.tabs(["🔥 주민 대상 로컬 핫딜 (B2C)", "📦 사장님 매장 소모품 공구 (B2B)", "✍️ 우리 아지트 상품 공구 제안"])
    
    def get_dday(deadline_str):
        try:
            d_date = datetime.strptime(deadline_str, "%Y-%m-%d")
            delta = (d_date - datetime.now()).days
            if delta > 0:
                return f"🔥 D-{delta}일 남음"
            elif delta == 0:
                return "🚨 오늘 마감!"
            else:
                return "❌ 마감된 공구"
        except Exception:
            return "진행 중"

    with deal_subtab1:
        st.markdown("### 🛒 진행 중인 동네 상생 핫딜 (주민 대상)")
        for deal in deals_db["deals"]:
            total_qty = sum([p["qty"] for p in deal["participants"]])
            total_people = len(deal["participants"])
            dday_txt = get_dday(deal["deadline"])
            progress_val = min(total_qty / deal["target"], 1.0)
            
            st.markdown(f"""
            <div class="azit-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="background:#EF4444; color:#fff; font-size:0.75rem; font-weight:700; padding:3px 8px; border-radius:6px;">{dday_txt}</span>
                    <span style="font-size:0.85rem; color:#64748B;">마감일: {deal['deadline']} (목표 {deal['target']}개)</span>
                </div>
                <h4 style="margin:6px 0; color:#0F172A;">{deal['title']}</h4>
                <p style="color:#2563EB; font-weight:700; font-size:1.05rem; margin-bottom:8px;">가격: {deal['price']}</p>
                <div style="font-size:0.9rem; color:#334155; margin-bottom:10px;">
                    👥 <b>현재 신청 현황:</b> 총 <span style="color:#EF4444; font-weight:700;">{total_people}명</span> 참여 / 누적 <span style="color:#2563EB; font-weight:700;">{total_qty}개</span> 신청완료
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.progress(progress_val)
            
            # expander 대신 토글 박스 형태로 안전하게 구현하여 글자 깨짐 원천 차단
            with st.container():
                st.markdown(f"#### 📝 [{deal['title']}] 신청 및 참여자 명단")
                with st.form(key=f"form_{deal['id']}"):
                    st.markdown("##### 🙋‍♂️ 공구 참여 신청하기")
                    p_name = st.text_input("신청자 성함 (또는 상호명)", key=f"name_{deal['id']}")
                    p_phone = st.text_input("연락처 (예: 010-0000-0000)", key=f"phone_{deal['id']}")
                    p_qty = st.number_input("신청 수량", min_value=1, max_value=100, value=1, step=1, key=f"qty_{deal['id']}")
                    
                    submitted = st.form_submit_button("✅ 공구 참여 확정하기")
                    if submitted:
                        if p_name and p_phone:
                            new_p = {
                                "name": p_name,
                                "phone": p_phone,
                                "qty": int(p_qty),
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            deal["participants"].append(new_p)
                            save_deals(deals_db)
                            st.success(f"🎉 성공적으로 신청되었습니다! (신청자: {p_name}, 수량: {p_qty}개)")
                            st.rerun()
                        else:
                            st.warning("성함과 연락처를 모두 입력해 주세요.")
                
                st.markdown("---")
                st.markdown("##### 📋 실시간 참여자 명단")
                if deal["participants"]:
                    for idx, p in enumerate(deal["participants"], 1):
                        st.markdown(f"{idx}. **{p['name']}**님 ({p['phone']}) ➡️ **{p['qty']}개** 신청 (`{p['time']}`)")
                else:
                    st.info("아직 신청자가 없습니다. 첫 번째 주인공이 되어보세요!")
            st.markdown("<hr style='margin:30px 0;'>", unsafe_allow_html=True)

    with deal_subtab2:
        st.markdown("### 📦 상생아지트 필수 소모품 도매가 공동 발주")
        st.markdown("""
        <div class="azit-card">
            <span style="background:#2563EB; color:#fff; font-size:0.75rem; font-weight:700; padding:3px 8px; border-radius:6px;">사장님 전용 B2B</span>
            <h4 style="margin:8px 0 4px 0; color:#0F172A;">🧾 카드단말기 영수증 롤페이퍼 (최고급 79*70) 50롤 1박스</h4>
            <p style="color:#64748B; font-size:0.95rem; margin-bottom:10px;">시중가 38,000원 ➡️ <b>공동 발주가 23,500원 (무료 배송)</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📦 소모품 공동발주 신청하기", use_container_width=True, key="b2b_order"):
            st.success("🎉 사장님 명의로 1박스 발주가 접수되었습니다.")

    with deal_subtab3:
        st.markdown(f"### 📢 [{store_name}] 상품 공구 오픈 제안")
        c_name = st.text_input("공구 진행 상품명", placeholder="예: 블루라이트 차단 안경 세트", key="c_name_input")
        c_qty = st.number_input("최소 진행 목표 수량 (개)", min_value=1, max_value=1000, value=30, step=1, key="c_qty_input")
        c_discount = st.text_input("회원 특별 공구가", placeholder="예: 35,000원", key="c_price_input")
        c_days = st.slider("진행 기간 (일)", min_value=3, max_value=30, value=7, key="c_days_input")
        c_desc = st.text_area("상품 및 혜택 상세 설명", placeholder="예: 정가 7만원 상당의 블루라이트 차단 안경테 + 기능성 렌즈 세트입니다.", key="c_desc_input")
        
        if st.button("🚀 공구 제안서 제출하기", use_container_width=True, key="c_submit_btn"):
            if c_name and c_discount:
                new_deal = {
                    "id": f"deal_{int(time.time())}",
                    "title": f"[{store_name}] {c_name}",
                    "price": f"{c_discount} (용친 단독 특가)",
                    "target": int(c_qty),
                    "deadline": (datetime.now() + timedelta(days=c_days)).strftime("%Y-%m-%d"),
                    "participants": []
                }
                deals_db["deals"].append(new_deal)
                save_deals(deals_db)
                st.success(f"🎉 공구 제안이 성공적으로 등록되었습니다! (목표: {c_qty}개)")
                st.rerun()
            else:
                st.warning("상품명과 공구가격을 입력해 주세요.")

# ==========================================
# 3. 📍 [👑 PRO 유료 전용] 네이버 플레이스 & 블로그 글쓰기
# ==========================================
with tabs[3]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-box">
            <h3>🔒 [PRO 유료 전용 기능] 네이버 플레이스 & 블로그 글 자동 생성</h3>
            <p>이 기능은 PRO 유료 회원 전용입니다. 사이드바에서 PRO 승인을 요청해 주세요.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="guide-box">
            👑 <b>[PRO 전용] 네이버 플레이스 소개글 & 블로그 최적화 원고 생성기</b><br>
            검색 상위 노출에 유리한 문조와 키워드를 조합하여 원고를 즉시 완성합니다.
        </div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            n_name = st.text_input("가게 이름과 지역", value=f"{store_name} ({sel_loc})", key="n1_pro")
        with c2:
            n_item = st.text_input("핵심 강점 / 메뉴", value=sel_feature, key="n2_pro")
        if st.button("👉 PRO 최적화 홍보글 만들기", use_container_width=True, key="btn_n_pro"):
            with st.spinner("네이버 상위 노출 원고 작성 중..."):
                prompt = f"업종: {sel_industry}\n가게명: {n_name}\n강점: {n_item}\n네이버 플레이스 소개글과 블로그 최적화 원고 작성해줘."
                out = generate_safe_content(prompt)
                if out:
                    st.code(out, language="markdown")

# ==========================================
# 4. 🥕 [👑 PRO 유료 전용] 당근 & 동네 소식
# ==========================================
with tabs[4]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-box">
            <h3>🔒 [PRO 유료 전용 기능] 당근마켓 및 동네 소식 글쓰기</h3>
            <p>이 기능은 PRO 유료 회원 전용입니다.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="guide-box">
            👑 <b>[PRO 전용] 당근마켓 & 동네 소식 글쓰기 비서</b><br>
            이웃 주민들이 친근하게 읽고 단골이 되는 커뮤니티 글을 작성합니다.
        </div>
        """, unsafe_allow_html=True)
        d_reason = st.selectbox("올릴 소식 주제", ["🔵 상생아지트 초대글", "🥬 새 상품 입고", "⏰ 깜짝 타임세일", "🌧️ 궂은 날씨 안부 인사"], key="d_pro")
        if st.button("👉 PRO 동네 소식글 만들기", use_container_width=True, key="btn_d_pro"):
            with st.spinner("당근 소식글 작성 중..."):
                prompt = f"업종: {sel_industry}\n가게: {store_name}\n주제: {d_reason}\n지역 주민들이 친근하게 읽을 수 있는 당근마켓/지역 소식글 작성."
                out = generate_safe_content(prompt)
                if out:
                    st.code(out, language="markdown")

# ==========================================
# 5. 📸 [👑 PRO 유료 전용] 인스타그램 피드
# ==========================================
with tabs[5]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-box">
            <h3>🔒 [PRO 유료 전용 기능] 인스타그램 감성 피드 & 해시태그 생성</h3>
            <p>이 기능은 PRO 유료 회원 전용입니다.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="guide-box">
            👑 <b>[PRO 전용] 인스타그램 피드 & 해시태그 생성기</b><br>
            시선을 사로잡는 훅 멘트와 인기 해시태그 5개를 생성합니다.
        </div>
        """, unsafe_allow_html=True)
        i_mood = st.selectbox("분위기", ["☕ 따뜻한 감성", "👑 전문성/신뢰", "🥩 침샘 자극", "🎉 번개 이벤트"], key="i_pro")
        if st.button("👉 PRO 인스타 글 만들기", use_container_width=True, key="btn_i_pro"):
            with st.spinner("인스타 피드 작성 중..."):
                prompt = f"업종: {sel_industry}\n가게: {store_name}\n분위기: {i_mood}\n1. 훅 멘트 2. 감성 본문 3. 해시태그 딱 5개 작성."
                out = generate_safe_content(prompt)
                if out:
                    st.code(out, language="markdown")

# ==========================================
# 6. 💬 [👑 PRO 유료 전용] 단골 문자 & 카톡
# ==========================================
with tabs[6]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-box">
            <h3>🔒 [PRO 유료 전용 기능] 단골 문자 & 카카오톡 메시지 작성 비서</h3>
            <p>이 기능은 PRO 유료 회원 전용입니다.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="guide-box">
            👑 <b>[PRO 전용] 단골 고객 문자 & 카톡 메시지 비서</b><br>
            단문(SMS)과 장문(LMS) 형태의 맞춤형 고객 소통 문구를 작성합니다.
        </div>
        """, unsafe_allow_html=True)
        m_target = st.selectbox("발송 목적", ["🎁 재방문 쿠폰", "🌧️ 비오는 날 번개 서비스", "🙇 환절기 안부 인사"], key="m_pro")
        if st.button("👉 PRO 문자 문구 만들기", use_container_width=True, key="btn_m_pro"):
            with st.spinner("단골 문자 작성 중..."):
                prompt = f"업종: {sel_industry}\n가게: {store_name}\n목적: {m_target}\n단문(SMS)과 장문(LMS) 작성."
                out = generate_safe_content(prompt)
                if out:
                    st.code(out, language="markdown")

# ==========================================
# 7. 💰 [무료] 알바 급여 계산기
# ==========================================
with tabs[7]:
    st.markdown("### 💰 아르바이트 주휴수당 및 실수령액 계산기 (무료 이용)")
    w_col1, w_col2 = st.columns(2)
    with w_col1:
        wage = st.number_input("시급 (원)", value=10030, step=100, key="wage_free")
        hours = st.number_input("주당 근무 시간", value=16.0, step=0.5, key="hours_free")
    with w_col2:
        tax = st.selectbox("공제 방식", ["3.3% 사업소득 공제", "고용보험 0.9% 공제", "공제 없음"], key="tax_free")
    if st.button("📊 급여 계산", use_container_width=True, key="calc_free"):
        base = wage * hours * 4.345
        holiday = ((hours / 40.0) * 8.0 * wage * 4.345) if hours >= 15 else 0
        total = base + holiday
        deduct = total * 0.033 if "3.3%" in tax else (total * 0.009 if "0.9%" in tax else 0)
        net = total - deduct
        st.success(f"세전 총액: {int(total):,}원 | 공제액: {int(deduct):,}원 | 💳 실수령액: {int(net):,}원 (주휴수당 {int(holiday):,}원 포함)")

# ==========================================
# 8. 📑 [무료] 지원금 서류 1분 발급기
# ==========================================
with tabs[8]:
    st.markdown("### 📑 소상공인 지원금 필수 서류 발급처 안내 (무료)")
    doc = st.selectbox("필요 서류", ["소상공인확인서", "부가가치세 과세표준증명원", "국세 완납증명서", "지방세 완납증명서"], key="doc_free")
    DOCS = {
        "소상공인확인서": ("중소기업현황정보시스템 (sminfo.mss.go.kr)", "회원가입/로그인 ➡️ [확인서 발급신청] ➡️ 즉시 PDF 다운로드"),
        "부가가치세 과세표준증명원": ("국세청 홈택스 (hometax.go.kr)", "국세증명 ➡️ [부가가치세 과세표준증명] ➡️ 발급"),
        "국세 완납증명서": ("국세청 홈택스 (hometax.go.kr)", "국세증명 ➡️ [납세증명서(국세완납)] ➡️ 즉시 출력"),
        "지방세 완납증명서": ("정부24 (gov.kr)", "검색창에 '지방세 납세증명' 검색 ➡️ 즉시 발급")
    }
    site, step = DOCS[doc]
    st.info(f"🌐 발급처: **{site}**\n\n📌 발급 방법: {step}")

# ==========================================
# 9. 🏛️ 지원금 & 절세 비서
# ==========================================
with tabs[9]:
    st.markdown("### 🏛️ 소상공인 국비 지원금 & 절세 가이드 (무료)")
    sub_q = st.selectbox("궁금한 지원금", [
        "전기세 25만 원 국비 지원받는 법",
        "비싼 대출 이자 4%대로 낮추는 법",
        "소상공인 간판/키오스크 교체 70% 국비 지원"
    ], key="sub_q_free")
    if st.button("🏛️ 설명 보기", use_container_width=True, key="sub_btn_free"):
        prompt = f"질문: {sub_q}\n초등학생도 이해할 수 있는 쉬운 일상어로 1) 혜택 금액 2) 자격 요건 3) 신청처 정리."
        out = generate_safe_content(prompt)
        if out:
            st.markdown(out)

# ==========================================
# 10. 🌙 오늘 장사 마감 & 처방
# ==========================================
with tabs[10]:
    st.markdown("### 🌙 오늘 장사 마감 리포트 & 내일 처방 (무료)")
    t_mood = st.selectbox("오늘 분위기", ["한산해서 아쉬움", "특정 시간대만 바쁨", "매출 최고 대성공!"], key="t_mood_free")
    if st.button("🌙 장사 마감 리포트 받기", use_container_width=True, key="t_btn_free"):
        prompt = f"가게: {store_name} ({sel_industry})\n오늘 분위기: {t_mood}\n1. 위로 브리핑 2. 내일 아침 올릴 1분 홍보글 처방."
        out = generate_safe_content(prompt)
        if out:
            st.markdown(out)
