import os
import sys
import time
import json
from datetime import datetime, timedelta

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import streamlit as st
from google import genai
from google.genai import errors

# ==========================================
# 🔑 [관리자 키 설정]
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

TRIAL_FILE = "trial_records.json"

def load_records():
    if os.path.exists(TRIAL_FILE):
        try:
            with open(TRIAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_records(data):
    try:
        with open(TRIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# 페이지 기본 설정
st.set_page_config(
    page_title="매장비서 AI | 소상공인 마케팅 도우미",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 큰 글씨, 시원하고 직관적인 디자인 (어르신 눈높이 맞춤)
st.markdown("""
<style>
    html, body, [class*="css"]  { font-size: 16px; }
    .main-title { font-size: 2rem; font-weight: 800; color: #1E293B; margin-bottom: 6px; }
    .sub-title { font-size: 1.05rem; color: #475569; margin-bottom: 20px; line-height: 1.5; }
    .guide-box { background: #F1F5F9; border-left: 5px solid #2563EB; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px; font-size: 1rem; color: #334155; }
    .stButton>button { height: 3.2rem; font-size: 1.15rem !important; font-weight: bold !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# 사이드바 (인증 제어만 심플하게 유지)
with st.sidebar:
    st.markdown("## 🏪 매장비서 AI")
    st.caption("우리 가게 손님 늘려주는 자동 글쓰기")
    st.markdown("---")
    
    st.markdown("### 🔑 서비스 시작하기")
    user_access_code = st.text_input("접속 코드 입력", value="free7")
    
    is_admin = False
    store_id = ""
    
    if user_access_code.strip() == "dream1215":
        st.success("👑 관리자님, 환영합니다! (무제한 사용)")
        is_admin = True
    elif user_access_code.strip() == "free7":
        store_id = st.text_input("가게 이름 (상호명)", placeholder="예: 삼촌네식당")
        if not store_id:
            st.warning("👉 가게 이름을 적어주셔야 7일 무료 체험이 시작됩니다.")
            st.stop()
            
        records = load_records()
        now = datetime.now()
        store_key = store_id.strip()
        
        if store_key not in records:
            records[store_key] = {
                "start_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "count": 0
            }
            save_records(records)
            first_time = now
        else:
            first_time = datetime.strptime(records[store_key]["start_time"], "%Y-%m-%d %H:%M:%S")
            
        expire_time = first_time + timedelta(days=7)
        remaining = expire_time - now
        
        if remaining.total_seconds() <= 0:
            st.error(f"""
            🔒 **[{store_key}] 사장님, 7일 무료 체험이 끝났습니다.**
            
            월 15,000원에 계속해서 손님을 부르는 글을 작성해보세요!
            (문의: 관리자에게 연락)
            """)
            st.stop()
        else:
            days = remaining.days
            hours = remaining.seconds // 3600
            st.success(f"🟢 **7일 무료 이용 중** (남은 시간: {days}일 {hours}시간)")
    else:
        st.error("올바른 코드를 넣어주세요.")
        st.stop()

    st.markdown("---")
    st.caption("© 2026 StoreMate AI. All rights reserved.")

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

SYSTEM_DIRECTIVE = """
너는 대한민국 골목상권 자영업 사장님들을 돕는 20년 경력의 친절하고 노련한 마케팅 전문가다.
- 사장님이 복잡한 설명을 하지 않아도 의도를 찰떡같이 알아듣고 완성도 높은 홍보글을 써준다.
- 손님들이 봤을 때 군침이 돌거나 신뢰가 팍팍 가는 맛깔난 어휘를 쓴다.
- 없는 가짜 위치나 거짓말은 절대 지어내지 않는다.
- 사장님이 바로 복사해서 올릴 수 있게 군더더기 없는 완성본으로 출력한다.
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

# 메인 헤더
st.markdown('<div class="main-title">🏪 매장비서 AI (글쓰기 도우미)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">가게 이름만 넣고 아래 파란 버튼을 누르면 <b>손님 부르는 홍보글</b>이 3초 만에 완성됩니다.</div>', unsafe_allow_html=True)

# 5개 핵심 메뉴
tabs = st.tabs([
    "📍 네이버 지도 & 블로그 글",
    "🥕 당근마켓 우리동네 알리기",
    "📸 인스타그램 사진 올릴 때",
    "💬 단골 문자 & 카톡 보내기",
    "🛡️ 속상한 손님 리뷰/악플 답글"
])

# ========================================================
# 1. 네이버 지도 & 블로그
# ========================================================
with tabs[0]:
    st.markdown('<div class="guide-box">💡 <b>네이버에 우리 가게 등록할 때</b>나, <b>블로그에 매장 홍보할 때</b> 그대로 복사해서 쓰시면 됩니다.</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        n_name = st.text_input("가게 이름과 동네 이름", placeholder="예: 바른식당 (용인 처인구 이동읍)", key="n1")
    with c2:
        n_type = st.selectbox("어떤 업종인가요?", [
            "식당 / 고깃집 / 포차 / 주점",
            "카페 / 빵집 / 디저트",
            "미용실 / 네일샵 / 뷰티",
            "안경원 / 의류 / 소매점",
            "카센터 / 수리 / 인테리어 / 설비",
            "헬스장 / 학원 / 기타"
        ], key="n2")
        
    n_item = st.text_input("우리 집 대표 메뉴나 자랑거리 (간단히)", placeholder="예: 볏짚 삼겹살과 된장찌개 맛집 / 친절하고 편안한 피팅", key="n3")
    
    if st.button("👉 네이버 홍보글 3초 만에 만들기", use_container_width=True, key="btn_n"):
        if not n_name:
            st.warning("가게 이름을 먼저 적어주세요!")
        else:
            with st.spinner("손님들이 많이 찾는 네이버 맞춤 글을 작성하고 있습니다..."):
                prompt = f"""
                업종: {n_type}
                가게명 및 지역: {n_name}
                자랑거리: {n_item if n_item else '정성 가득한 맛과 친절한 서비스'}

                다음 2가지를 사장님이 그대로 복사해서 쓸 수 있게 써줘:
                1. [네이버 지도 매장 소개글] (손님이 스마트폰으로 볼 때 한눈에 반하게 300~400자 내외)
                2. [네이버 블로그 추천 글] (검색 잘 걸리는 제목 2개 + 찾아오고 싶게 만드는 본문 글)
                """
                output = generate_safe_content(prompt)
                if output:
                    st.success("🎉 글이 완성되었습니다! 아래 네모 박스 내용을 복사해서 사용하세요.")
                    st.code(output, language="markdown")

# ========================================================
# 2. 당근마켓 동네 알리기 (분류 8종)
# ========================================================
with tabs[1]:
    st.markdown('<div class="guide-box">💡 <b>걸어서 10분 거리의 동네 주민들</b>에게 오늘 우리 가게 소식을 친근하게 전해보세요.</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        d_name = st.text_input("가게 이름과 동네", placeholder="예: 우리집식당 (이동읍 송전리)", key="d1")
    with c2:
        d_benefit = st.text_input("이웃에게 줄 작은 혜택 (선택)", placeholder="예: 당근 보고 오시면 음료수 한 캔 서비스 / 2,000원 할인", key="d2")
        
    d_reason = st.selectbox("어떤 내용으로 올릴까요? (상황 선택)", [
        "🥬 오늘 들어온 신선한 재료 / 새 상품 입고 알림",
        "⏰ 오늘만 깜짝 마감 할인 / 타임 세일 (당일 재고 소진)",
        "🎁 당근 이웃 첫 방문 & 단골 맺기 전용 혜택 소식",
        "🌧️ 비/눈 오는 날 또는 궂은 날씨 동네 안부",
        "🍽️ 신메뉴 출시 / 새로운 서비스 개시 알림",
        "👨‍🍳 사장님의 정직한 장사 일기 (진심과 정성 어필)",
        "📢 정기 휴무 공지 / 명절·공휴일 정상 영업 안내",
        "💡 동네 주민들을 위한 생활 꿀팁 / 무료 점검·상담 안내"
    ], key="d3")
    
    if st.button("👉 당근마켓 소식글 만들기", use_container_width=True, key="btn_d"):
        if not d_name:
            st.warning("가게 이름을 적어주세요!")
        else:
            with st.spinner("동네 이웃들이 좋아하는 다정한 글로 작성 중입니다..."):
                prompt = f"""
                가게: {d_name}
                혜택: {d_benefit if d_benefit else '정성 가득한 서비스'}
                선택한 주제: {d_reason}

                당근마켓 동네생활/비즈프로필에 올릴 글을 써줘.
                - 광고 느낌 없이, 동네 이웃에게 직접 다정하게 말 건네듯 솔직하고 따뜻한 어조.
                - 선택한 주제({d_reason})의 핵심 내용이 첫 줄부터 바로 와닿게 작성.
                - 끝부분에 부담 없이 들러주시라는 친근한 인사와 당근 단골 맺기 안내 포함.
                """
                output = generate_safe_content(prompt)
                if output:
                    st.success("🎉 당근 글 완성! 복사해서 당근마켓 앱에 붙여넣으세요.")
                    st.code(output, language="markdown")

# ========================================================
# 3. 인스타그램 사진 올릴 때 (분위기 8종)
# ========================================================
with tabs[2]:
    st.markdown('<div class="guide-box">💡 매장에서 <b>음식이나 상품 사진 한 장 찍고</b> 올릴 때, 붙여넣기만 하면 되는 감성 글입니다.</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        i_name = st.text_input("가게 이름과 대표 메뉴/상품", placeholder="예: 카페블룸 (딸기라떼) / 바른안경 (가벼운 뿔테)", key="i1")
    with c2:
        i_mood = st.selectbox("원하는 인스타 분위기 선택", [
            "🥩 군침 도는 침샘 자극 (오감 자극, 비주얼 극찬)",
            "☕ 따뜻하고 포근한 힐링 감성 (여유로운 아지트 느낌)",
            "🍺 퇴근길 위로와 낭만 (오늘 하루 고생한 직장인 타겟)",
            "🔥 활기차고 에너지 넘치는 유쾌한 분위기 (젊은 감각)",
            "👑 20년 내공의 장인/전문성 (정직한 재료, 꼼꼼한 기술)",
            "🌧️ 비 오는 날 빗소리와 함께 젖어드는 감성",
            "🎉 깜짝 특가 / 오늘만 드리는 번개 혜택 소식",
            "🌿 소소하고 정직한 사장님의 일상 일기 (공감 유발)"
        ], key="i2")
        
    if st.button("👉 인스타 글 + 해시태그 만들기", use_container_width=True, key="btn_i"):
        if not i_name:
            st.warning("가게 이름과 메뉴를 적어주세요!")
        else:
            with st.spinner("선택하신 분위기에 딱 맞춘 글을 만들고 있습니다..."):
                prompt = f"""
                가게 및 메뉴: {i_name}
                선택한 분위기: {i_mood}

                인스타그램 사진 1장과 함께 올릴 피드 글을 작성해줘:
                1. 첫 줄에 눈길을 끄는 매력적인 훅(Hook) 문장
                2. {i_mood}의 톤앤매너가 완벽히 살아있는 본문 문구 (3~4줄로 줄바꿈 깔끔하게)
                3. 팔로워들이 댓글을 남기게 만드는 소통형 질문 1개
                4. 인스타 돋보기 검색에 잘 걸리는 로컬 타겟팅 해시태그 25개
                """
                output = generate_safe_content(prompt)
                if output:
                    st.success("🎉 인스타 글 완성! 복사해서 인스타에 그대로 올리세요.")
                    st.code(output, language="markdown")

# ========================================================
# 4. 단골 문자 & 카톡 보내기 (재방문 유도 신설)
# ========================================================
with tabs[3]:
    st.markdown('<div class="guide-box">💡 기존 손님들에게 <b>스팸 느낌 없이 반갑게</b> 보낼 수 있는 재방문 유도 문자/카톡입니다.</div>', unsafe_allow_html=True)
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        m_name = st.text_input("가게 이름", placeholder="예: 바른갈비 / 미소헤어", key="m1")
    with m_col2:
        m_target = st.selectbox("어떤 상황인가요?", [
            "🎁 오랜만에 생각나서 드리는 [재방문 감사 쿠폰]",
            "🌧️ 비/눈 오는 날 깜짝 번개 서비스 (오늘만 음료/사이드 제공)",
            "🍲 신메뉴 / 신제품 출시 기념 VIP 단골 시식 초대",
            "🙇 명절 / 새해 / 연말 정성스러운 감사 안부 인사",
            "🎂 생일 / 기념일 축하 특별 우대 멘트"
        ], key="m2")
        
    m_gift = st.text_input("손님에게 드릴 혜택 (선택)", placeholder="예: 재방문 시 테이블당 음료 1병 무료 / 시술 10% 우대", key="m3")
    
    if st.button("👉 단골 문자 & 카톡 문구 만들기", use_container_width=True, key="btn_m"):
        if not m_name:
            st.warning("가게 이름을 먼저 적어주세요!")
        else:
            with st.spinner("손님이 기분 좋게 열어보는 안부 문자를 작성 중입니다..."):
                prompt = f"""
                가게명: {m_name}
                발송 상황: {m_target}
                제공 혜택: {m_gift if m_gift else '감사한 마음을 담은 정성 가득한 서비스'}

                다음 2가지 버전으로 깔끔하게 작성해줘:
                1. [짧은 문자용 (SMS)]
                   - 45자 내외로 핵심 혜택과 안부만 군더더기 없이 딱 들어간 형태
                2. [카카오톡 / 장문 문자용 (LMS)]
                   - 읽는 사람의 마음이 따뜻해지는 다정한 문체
                   - 스팸 광고 느낌을 완전히 배제하고 진심 어린 안부와 혜택 안내
                   - 마지막에 편안하게 방문하시라는 정중한 맺음말
                """
                output = generate_safe_content(prompt)
                if output:
                    st.success("🎉 문자 문구가 완성되었습니다! 복사해서 손님들에게 전송하세요.")
                    st.code(output, language="markdown")

# ========================================================
# 5. 속상한 손님 리뷰/악플 답글
# ========================================================
with tabs[4]:
    st.markdown('<div class="guide-box">💡 손님이 별점을 낮게 주거나 불만 리뷰를 남겼을 때, <b>화내지 않고 점잖게 대처하는 모범 답글</b>입니다.</div>', unsafe_allow_html=True)
    
    r_name = st.text_input("가게 이름", placeholder="예: 정성식당", key="r1")
    r_text = st.text_area("손님이 남긴 리뷰를 여기에 그대로 붙여넣으세요", placeholder="예: 맛은 있는데 주문하고 너무 늦게 나와서 기분 상했네요.", height=100, key="r2")
    
    if st.button("👉 점잖고 품격 있는 답글 만들기", use_container_width=True, key="btn_r"):
        if not r_name or not r_text:
            st.warning("가게 이름과 손님 리뷰를 모두 넣어주세요!")
        else:
            with st.spinner("다른 손님들이 봐도 사장님 편을 들 수 있는 정중한 답글을 작성 중입니다..."):
                prompt = f"""
                가게: {r_name}
                손님 불만 리뷰: {r_text}

                이 리뷰를 읽고 방문을 망설일 다른 수백 명의 손님들을 안심시키는 프로 사장님의 답글을 써줘.
                - 억울하거나 화내지 않고, 정중하고 예의 바르게 사과 및 개선 약속.
                - 읽는 사람이 '아, 이 집 사장님 참 양심적이고 대처가 멋지시네' 하고 믿음이 가도록 작성.
                """
                output = generate_safe_content(prompt)
                if output:
                    st.success("🎉 답글이 완성되었습니다! 복사해서 리뷰에 달아주세요.")
                    st.code(output, language="markdown")