import streamlit as st
import pandas as pd

# 모바일 화면 확대/축소(Pinch to Zoom) 가능하도록 설정 변경
st.set_page_config(
    page_title="경기지역본부 명단", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 모바일 및 PC에서 카테고리 칸들이 오른쪽으로 넘치지 않고 컴팩트하게 좌우 배치되도록 CSS 최적화
st.markdown("""
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    </head>
    <style>
    .stApp { padding: 10px; }
    /* 셀렉트박스(카테고리) 영역이 화면 밖으로 넘치지 않도록 내부 간격 및 폭 조절 */
    [data-testid="column"] {
        padding: 0px 4px !important;
        flex: 1 !important;
        min-width: 0 !important;
    }
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

# 주요 컬럼 위치 인덱스
NAME_IDX = 2
BRANCH_IDX = 3
PHONE_IDX = 6
RENTAL_IDX = 9
PRIME_IDX = 10
SITE_IDX = 11
STATUS_IDX = 19
NOTE_RENTAL_IDX = 23 # 비고(임대사)
NOTE_PRIME_IDX = 24  # 비고(원청사)

# UI 검색 필터 및 안내 문구
search_query = st.text_input("🔍 통합 검색 (이름, 현장명, 원청사, 임대사)", "")
st.caption("💡 검색어 입력 후 **Enter**를 누르면 검색이 적용됩니다.")

# --- 카테고리 검색란: 2x2 그리드 배치 (좌우로 2개씩, 위아래로 2줄) ---
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    raw_branches = []
    for val in df.iloc[:, BRANCH_IDX]:
        cleaned_val = str(val).strip()
        if cleaned_val and cleaned_val != 'nan' and cleaned_val not in raw_branches:
            raw_branches.append(cleaned_val)
    raw_branches = sorted(raw_branches)
    selected_branch = st.selectbox("소속지부/본부", ["전체"] + raw_branches)

with row1_col2:
    selected_status = st.selectbox("대기유무", ["전체", "취업 중", "대기자"])

with row2_col1:
    prime_list = []
    for _, row in df.iterrows():
        p_val = row.iloc[NOTE_PRIME_IDX] if row.iloc[NOTE_PRIME_IDX] else row.iloc[PRIME_IDX]
        p_val_str = str(p_val).strip()
        if p_val_str and p_val_str != 'nan' and p_val_str not in prime_list:
            prime_list.append(p_val_str)
    raw_primes = sorted(prime_list)
    selected_prime = st.selectbox("원청사", ["전체"] + raw_primes)

with row2_col2:
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
    for idx in [NAME_IDX, SITE_IDX, PRIME_IDX, RENTAL_IDX, NOTE_RENTAL_IDX, NOTE_PRIME_IDX, BRANCH_IDX]:
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
        site = row.iloc[SITE_IDX] if row.iloc[SITE_IDX] else '-'
        
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
            
        st.markdown(f"""
        <div class="member-card">
            <div class="member-name">
                {name} 
                <span class="tag">{branch}</span> 
                <span class="tag {status_class}">{status_text}</span>
            </div>
            <div class="member-info">📞 <b>연락처:</b> {phone}</div>
            <div class="member-info">🏗️ <b>현장명:</b> {site if site else '현장 없음 (대기 중)'}</div>
            <div class="member-info">🏢 <b>임대사/원청사:</b> {rental} / {prime}</div>
        </div>
        """, unsafe_allow_html=True)
