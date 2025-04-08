import streamlit as st
import json
import glob
import pandas as pd


st.set_page_config(layout="wide", page_title="Lang2SQL 평가 시각화")

# 스타일 적용
st.markdown(
    """
<style>
    .main {
        padding: 2rem;
    }
    .sql-code {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        white-space: pre-wrap;
    }
    .persona-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .persona-card h4 {
        color: #1f77b4;
        margin-top: 0;
    }
    .persona-card p {
        margin-bottom: 5px;
        color: #333;
    }
    pre {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    code {
        white-space: pre-wrap !important;
        overflow-x: visible !important;
        word-wrap: break-word !important;
    }
    .stCodeBlock {
        max-width: 100% !important;
        overflow-x: visible !important;
    }
    .block-container {
        max-width: 100% !important;
        padding-left: 5% !important;
        padding-right: 5% !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        overflow-x: visible !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 제목 설정
st.title("Lang2SQL 평가 결과 시각화")
st.markdown("SQL 생성 프로세스와 결과를 검토합니다.")


# JSON 파일 로드 함수
def load_json_files():
    json_files = glob.glob("data/q_sql/*.json")
    return json_files


# 선택된 파일로부터 데이터 로드
def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# 파일 선택
json_files = load_json_files()
if not json_files:
    st.error("eval_result_*.json 파일이 현재 디렉토리에 존재하지 않습니다.")
    st.stop()

selected_file = st.selectbox("평가 결과 파일 선택", json_files)
data = load_data(selected_file)

# 사이드바에 질문 목록 표시
st.sidebar.title("질문 목록")
selected_q_index = st.sidebar.radio(
    "질문을 선택하세요:",
    options=range(len(data["questions"])),
    format_func=lambda i: f"Q{i+1}: {data['questions'][i][:50]}...",
)

# 페르소나 정보 표시
st.header("페르소나 정보")
persona = data.get("persona", {})
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(
        f"""
    <div class="persona-card">
        <h4>{persona.get('name', '이름 없음')}</h4>
        <p><strong>부서:</strong> {persona.get('department', '정보 없음')}</p>
        <p><strong>역할:</strong> {persona.get('role', '정보 없음')}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
    <div class='persona-card'>
        <p>{persona.get('background', '배경 정보 없음')}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# 선택된 질문 및 답변 표시
st.header("질문 및 답변 세부 정보")

# 선택된 질문 표시
st.subheader("🔍 원본 질문")
st.markdown(f"**{data['questions'][selected_q_index]}**")

# 선택된 답변 가져오기
answer = data["answers"][selected_q_index]

# 탭으로 정리된 정보 표시
tabs = st.tabs(["SQL 결과", "질문 구체화", "검색된 테이블", "전체 SQL 생성 과정"])

# SQL 결과 탭
with tabs[0]:
    st.markdown("### 생성된 SQL 쿼리")
    sql_query = answer.get("answer_SQL", "SQL 쿼리가 없습니다.")
    st.code(sql_query, language="sql")

    st.markdown("### SQL 설명")
    st.markdown(answer.get("answer_explanation", "설명이 없습니다."))

    st.markdown("### 데이터베이스 환경")
    st.code(answer.get("user_database_env", "정보 없음"))

# 질문 구체화 탭
with tabs[1]:
    refined_question = answer.get("question_refined", "질문 구체화 정보가 없습니다.")
    st.markdown(refined_question)

# 검색된 테이블 탭
with tabs[2]:
    searched_tables = answer.get("searched_tables", {})

    if searched_tables:
        for table_name, table_info in searched_tables.items():
            with st.expander(f"테이블: {table_name}"):
                st.markdown(
                    f"**설명:** {table_info.get('table_description', '설명 없음')}"
                )

                # 테이블 컬럼 정보를 DataFrame으로 변환하여 표시
                columns_data = []
                for col_name, col_desc in table_info.items():
                    if col_name != "table_description":
                        columns_data.append({"컬럼명": col_name, "설명": col_desc})

                if columns_data:
                    st.table(pd.DataFrame(columns_data))
                else:
                    st.info("컬럼 정보가 없습니다.")
    else:
        st.info("검색된 테이블 정보가 없습니다.")

# 전체 SQL 생성 과정 탭
with tabs[3]:
    st.markdown("### 질문에서 SQL까지의 전체 과정")

    st.markdown("#### 1. 원본 질문")
    st.markdown(f"> {data['questions'][selected_q_index]}")

    st.markdown("#### 2. 질문 구체화")
    st.markdown(answer.get("question_refined", "질문 구체화 정보가 없습니다."))

    st.markdown("#### 3. 검색된 테이블")
    table_names = list(answer.get("searched_tables", {}).keys())
    st.markdown(", ".join(table_names) if table_names else "테이블 정보 없음")

    st.markdown("#### 4. 생성된 SQL")
    st.code(answer.get("answer_SQL", "SQL 쿼리가 없습니다."), language="sql")

    st.markdown("#### 5. SQL 설명")
    st.markdown(answer.get("answer_explanation", "설명이 없습니다."))
