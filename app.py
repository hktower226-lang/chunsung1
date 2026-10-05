import streamlit as st
import pandas as pd

# 모바일 화면 확대/축소(Pinch to Zoom) 가능하도록 설정 변경
st.set_page_config(
    page_title="경기지역본부 명단", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 기본 스타일 설정
st.markdown("""
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    </head>
    <style>
    .stApp { padding: 10px; }
    .member-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 5px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .member-name { font-size: 18px; font-weight: bold; color: #111; }
    .member-info { font-size: 14px; color: #444; margin-top: 4px; }
    .tag {
        display: inline-block;
        background: #e9ecef;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 12px;
        margin-right: 5px;
    }
    .tag-status-work { background: #d1e7dd; color: #0f5132; }
    .tag-status-wait { background: #fff3cd; color: #664d03; }
    .tag-size { background: #cfe2ff; color: #084298; }
    </style>
""", unsafe_allow_html=True)

st.title("📱 경기지역본부 명단")

@st.cache_data(ttl=10)
def load_data():
    file_path = "경기지역본부명단.xlsx"
    raw_df = pd.read_excel(file_path, sheet_name=0, dtype=str)
    df = raw_df.iloc[2:].fillna('').copy()
    
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip().replace({'nan': '', 'None': ''})
        
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"엑셀 파일 읽기 오류: {e}")
    st.stop()

# 주요 컬럼 위치 인덱스 (엑셀 구조 반영)
NAME_IDX = 2
BRANCH_IDX = 3
PHONE_IDX = 6
HOME_ADDR_IDX = 8      # 거주 주소
RENTAL_IDX = 9
PRIME_IDX = 10
SITE_IDX = 11
STATUS_IDX = 19
SIZE_IDX = 20          # 대형/소형
NOTE_RENTAL_IDX = 23   # 비고(임대사)
NOTE_PRIME_IDX = 24    # 비고(원청사)
TOWER_COUNT_IDX = 25   # 현재 설치 타워수량
UNION_HANO_IDX = 26    # 한국타워크레인 조종사노동조합 (한노)
UNION_MINNO_IDX = 27   # 민주노총 건설노조 타워크레인분과 (민노)
UNION_EX_HANO_IDX = 28 # 건설노조(한노제명) 타워크레인분과 (건산)
UNION_NON_IDX = 29     # 비노조 및 직원 (비노)
MIDUNG_IDX = 30        # 미정
WAGE_IDX = 31          # 평균임금

# 숫자 데이터를 안전하게 포맷팅하는 헬퍼 함수
def safe_num(val):
    if not val or val == 'nan' or val == '':
        return '0'
    try:
        # 소수점 형태(.0)로 읽히는 경우 처리
        return str(int(float(val)))
    except:
        return str(val)

# UI 검색 필터 및 안내 문구
search_query = st.text_input("🔍 통합 검색 (이름, 현장명, 원청사, 임대사)", "")
st.caption("💡 검색어 입력 후 **Enter**를 누르면 검색이 적용됩니다.")

# --- 기존 세로 순서대로 정렬된 검색 카테고리 ---
# 1. 소속지부본부
raw_branches = []
for val in df.iloc[:, BRANCH_IDX]:
    cleaned_val = str(val).strip()
    if cleaned_val and cleaned_val != 'nan' and cleaned_val not in raw_branches:
        raw_branches.append(cleaned_val)
raw_branches = sorted(raw_branches)
selected_branch = st.selectbox("소속지부본부", ["전체"] + raw_branches)

# 2. 대기유무
selected_status = st.selectbox("대기유무", ["전체", "취업 중", "대기자"])

# 3. 원청사
prime_list = []
for _, row in df.iterrows():
    p_val = row.iloc[NOTE_PRIME_IDX] if row.iloc[NOTE_PRIME_IDX] else row.iloc[PRIME_IDX]
    p_val_str = str(p_val).strip()
    if p_val_str and p_val_str != 'nan' and p_val_str not in prime_list:
        prime_list.append(p_val_str)
raw_primes = sorted(prime_list)
selected_prime = st.selectbox("원청사", ["전체"] + raw_primes)

# 4. 임대사
rental_list = []
for _, row in df.iterrows():
    r_val = row.iloc[NOTE_RENTAL_IDX] if row.iloc[NOTE_RENTAL_IDX] else row.iloc[RENTAL_IDX]
    r_val_str = str(r_val).strip()
    if r_val_str and r_val_str != 'nan' and r_val_str not in rental_list:
        rental_list.append(r_val_str)
raw_rentals = sorted(rental_list)
selected_rental = st.selectbox("임대사", ["전체"] + raw_rentals)

# --- 자동 판단 로직 ---
is_site_exist = df.iloc[:, SITE_IDX].astype(str).str.strip() != ''
is_status_wait = df.iloc[:, STATUS_IDX].astype(str).str.contains('대기', na=False)
cond_is_wait = (~is_site_exist) | is_status_wait

# 데이터 필터링
filtered_df = df.copy()

# 지부 필터
if selected_branch != "전체":
    filtered_df = filtered_df[filtered_df.iloc[:, BRANCH_IDX].astype(str).str.strip() == selected_branch]

# 대기유무 필터
if selected_status == "취업 중":
    filtered_df = filtered_df[~cond_is_wait.reindex(filtered_df.index, fill_value=False)]
elif selected_status == "대기자":
    filtered_df = filtered_df[cond_is_wait.reindex(filtered_df.index, fill_value=False)]

# 원청사 필터
if selected_prime != "전체":
    prime_matched_indices = []
    for idx, row in filtered_df.iterrows():
        p_val = str(row.iloc[NOTE_PRIME_IDX] if row.iloc[NOTE_PRIME_IDX] else row.iloc[PRIME_IDX]).strip()
        if p_val == selected_prime:
            prime_matched_indices.append(idx)
    filtered_df = filtered_df.loc[prime_matched_indices]

# 임대사 필터
if selected_rental != "전체":
    rental_matched_indices = []
    for idx, row in filtered_df.iterrows():
        r_val = str(row.iloc[NOTE_RENTAL_IDX] if row.iloc[NOTE_RENTAL_IDX] else row.iloc[RENTAL_IDX]).strip()
        if r_val == selected_rental:
            rental_matched_indices.append(idx)
    filtered_df = filtered_df.loc[rental_matched_indices]

# 검색어 필터
if search_query:
    query_clean = search_query.replace(" ", "").lower()
    cond_search = pd.Series(False, index=filtered_df.index)
    for idx in [NAME_IDX, SITE_IDX, PRIME_IDX, RENTAL_IDX, NOTE_RENTAL_IDX, NOTE_PRIME_IDX, BRANCH_IDX, HOME_ADDR_IDX]:
        cond_search |= filtered_df.iloc[:, idx].astype(str).str.replace(" ", "").str.lower().str.contains(query_clean, na=False)
    filtered_df = filtered_df[cond_search]

st.markdown(f"**조회 결과:** 총 **{len(filtered_df)}** 명")
st.divider()

if len(filtered_df) == 0:
    st.info("해당하는 조건의 조합원이 없습니다.")
else:
    for idx, row in filtered_df.iterrows():
        name = row.iloc[NAME_IDX] if row.iloc[NAME_IDX] else '-'
        branch = row.iloc[BRANCH_IDX] if row.iloc[BRANCH_IDX] else '-'
        phone = row.iloc[PHONE_IDX] if row.iloc[PHONE_IDX] else '-'
        home_addr = row.iloc[HOME_ADDR_IDX] if row.iloc[HOME_ADDR_IDX] else '-'
        site = row.iloc[SITE_IDX] if row.iloc[SITE_IDX] else '-'
        size_val = row.iloc[SIZE_IDX] if row.iloc[SIZE_IDX] else '-'
        
        # 타워 수량 및 노조별 상세 대수 정보 (안전하게 숫자 변환)
        tower_count = safe_num(row.iloc[TOWER_COUNT_IDX])
        hano = safe_num(row.iloc[UNION_HANO_IDX])
        minno = safe_num(row.iloc[UNION_MINNO_IDX])
        ex_hano = safe_num(row.iloc[UNION_EX_HANO_IDX])
        non_union = safe_num(row.iloc[UNION_NON_IDX])
        midung = safe_num(row.iloc[MIDUNG_IDX])
        wage = row.iloc[WAGE_IDX] if row.iloc[WAGE_IDX] else '-'
        
        # 임대사/원청사 표시 (비고에 적혀있으면 비고값 우선 사용)
        rental_val = row.iloc[RENTAL_IDX]
        prime_val = row.iloc[PRIME_IDX]
        note_rental = row.iloc[NOTE_RENTAL_IDX]
        note_prime = row.iloc[NOTE_PRIME_IDX]
        
        rental = note_rental if note_rental else (rental_val if rental_val else '-')
        prime = note_prime if note_prime else (prime_val if prime_val else '-')
        
        # 상태 태그 (취업 중 / 대기자)
        if site != '-' and site != '':
            status_text = "취업 중"
            status_class = "tag-status-work"
        else:
            status_text = "대기자"
            status_class = "tag-status-wait"
            
        # 메인 카드 렌더링
        st.markdown(f"""
        <div class="member-card">
            <div class="member-name">
                {name} 
                <span class="tag">{branch}</span> 
                <span class="tag tag-size">{size_val}</span>
                <span class="tag {status_class}">{status_text}</span>
            </div>
            <div class="member-info">🏗️ <b>현장명:</b> {site if site else '현장 없음 (대기 중)'}</div>
            <div class="member-info">🏢 <b>임대사/원청사:</b> {rental} / {prime}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 세부내역 확인을 위한 Streamlit expander
        with st.expander(f"📋 {name} 님의 세부내역 보기"):
            st.markdown(f"""
            - 📞 **연락처:** {phone}
            - 🏠 **거주 주소지:** {home_addr}
            - 🏗️ **현재 설치 타워수량 총계:** {tower_count}대
              - ▫️ **한노:** {hano}대
              - ▫️ **민노:** {minno}대
              - ▫️ **건산:** {ex_hano}대
              - ▫️ **비노:** {non_union}대
              - ▫️ **미정:** {midung}대
            - 💰 **평균임금:** {wage}
            """)
