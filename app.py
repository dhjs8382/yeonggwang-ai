import streamlit as st
import google.generativeai as genai
import requests
from datetime import datetime, timedelta
import re

# --- 1. 설정 ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"] 
NEIS_API_KEY = st.secrets["NEIS_API_KEY"]

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-3.1-flash-lite-preview')

# 2. 급식 및 학사일정
def get_meal_by_day(target_date):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {"KEY": NEIS_API_KEY, "Type": "json", "ATPT_OFCDC_SC_CODE": "R10", "SD_SCHUL_CODE": "8750188", "MLSV_YMD": target_date}
    try:
        res = requests.get(url, params=params).json()
        if "mealServiceDietInfo" in res:
            rows = res['mealServiceDietInfo'][1]['row']
            return "\n".join([f"**[{r['MMEAL_SC_NM']}]**\n{r['DDISH_NM'].replace('<br/>', ', ')}" for r in rows])
        return "급식 정보 없음"
    except: return "급식 서버 에러"

def get_school_plan(start_date, end_date):
    url = "https://open.neis.go.kr/hub/SchoolSchedule"
    params = {"KEY": NEIS_API_KEY, "Type": "json", "ATPT_OFCDC_SC_CODE": "R10", "SD_SCHUL_CODE": "8750188", "AA_FROM_YMD": start_date, "AA_TO_YMD": end_date}
    try:
        res = requests.get(url, params=params).json()
        if "SchoolSchedule" in res:
            rows = res['SchoolSchedule'][1]['row']
            return "\n".join([f"- {r['AA_YMD'][4:6]}/{r['AA_YMD'][6:8]}: {r['EVENT_NM']}" for r in rows])
        return "조회된 일정 없음"
    except: return "학사일정 서버 에러"

# 3. 시간표
def get_timetable(target_date, grade, class_nm):
    url = "https://open.neis.go.kr/hub/hisTimetable"
    params = {
        "KEY": NEIS_API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "ATPT_OFCDC_SC_CODE": "R10", # 경북교육청
        "SD_SCHUL_CODE": "8750188",   # 영광고등학교
        "ALL_TI_YMD": target_date,    # 시간표일자
        "GRADE": grade,               # 학년
        "CLASS_NM": class_nm,         # 학급명
        "AY": target_date[:4]         # 학년도 (연도 추출)
    }
    
    try:
        res = requests.get(url, params=params).json()
        if "hisTimetable" in res:
            rows = res['hisTimetable'][1]['row']
            # 교시 순서대로 정렬
            rows.sort(key=lambda x: x['PERIO'])
            timetable_res = ""
            for r in rows:
                timetable_res += f"{r['PERIO']}교시: {r['ITRT_CNTNT']}\n"
            return timetable_res
        return "조회된 시간표가 없습니다. (주말, 공휴일 또는 미등록)"
    except:
        return "시간표 서버 연결 오류"

# 4. 웹 화면 구성 및 사이드바 설정
st.set_page_config(page_title="영광고 AI 비서", page_icon="🏫")

with st.sidebar:
    st.header("🏫 영광고 AI 가이드")
    st.info("오늘/내일 급식, 일정, 시간표를 물어보세요!")
    st.write("예: '내일 점심 뭐야?', '기말고사 언제야?', '내일 시간표 알려줘'")

    st.header("👤 내 정보 설정")
    my_grade = st.selectbox("학년", ["1", "2", "3"], index=0)
    my_class = st.text_input("반 (숫자만)", value="1")
    st.caption("반 정보를 입력하면 해당 반의 시간표를 보여줍니다.")

st.title("🏫 영광고등학교 AI 비서")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 질문 처리 로직
if prompt := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("데이터 분석 중..."):
            now = datetime.now()
            
            # 날짜 판별
            target_date = now
            if "내일" in prompt: target_date = now + timedelta(days=1)
            elif "어제" in prompt: target_date = now - timedelta(days=1)
            
            target_date_str = target_date.strftime("%Y%m%d")
            display_date = target_date.strftime("%Y년 %m월 %d일")
            
            # 데이터 수집
            meal_info = get_meal_by_day(target_date_str)
            plan_info = get_school_plan(now.strftime("%Y%m01"), (now + timedelta(days=31)).strftime("%Y%m%d"))
            timetable_info = get_timetable(target_date_str, my_grade, my_class)
            
            full_prompt = f"""
            너는 영광고등학교 AI 비서야.
            오늘 날짜: {now.strftime('%Y-%m-%d')}
            조회 대상: {display_date} ({my_grade}학년 {my_class}반)
            
            [시간표 정보]
            {timetable_info}
            
            [급식 정보]
            {meal_info}
            
            [이번 달 학사일정]
            {plan_info}
            
            질문: {prompt}
            위 정보를 바탕으로 친절하게 답변해줘.
            """
            
            try:
                response = model.generate_content(full_prompt)
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except:
                st.error("AI 응답 생성 중 오류가 발생했습니다.")