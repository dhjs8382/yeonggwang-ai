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

# --- 2. 나이스 API 함수들 ---

# [급식 정보]
def get_meal_by_day(target_date):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": NEIS_API_KEY, "Type": "json",
        "ATPT_OFCDC_SC_CODE": "R10", 
        "SD_SCHUL_CODE": "8750188",  
        "MLSV_YMD": target_date
    }
    try:
        res = requests.get(url, params=params).json()
        if "mealServiceDietInfo" in res:
            rows = res['mealServiceDietInfo'][1]['row']
            meal_result = ""
            for r in rows:
                meal_result += f"**[{r['MMEAL_SC_NM']}]**\n{r['DDISH_NM'].replace('<br/>', ', ')}\n\n"
            return meal_result
        return "해당 날짜의 급식 정보가 없습니다."
    except:
        return "급식 서버 연결 실패"

# [실시간 학사일정]
def get_school_plan(start_date, end_date):
    url = "https://open.neis.go.kr/hub/SchoolSchedule"
    params = {
        "KEY": NEIS_API_KEY, "Type": "json",
        "ATPT_OFCDC_SC_CODE": "R10",
        "SD_SCHUL_CODE": "8750188",
        "AA_FROM_YMD": start_date,
        "AA_TO_YMD": end_date
    }
    try:
        res = requests.get(url, params=params).json()
        if "SchoolSchedule" in res:
            rows = res['SchoolSchedule'][1]['row']
            plan_result = ""
            for r in rows:
                plan_result += f"- {r['AA_YMD']}: {r['EVENT_NM']}\n"
            return plan_result
        return "조회된 학사일정이 없습니다."
    except:
        return "학사일정 서버 연결 실패"

# [학년/반별 시간표]
def get_timetable(target_date, grade, class_nm):
    url = "https://open.neis.go.kr/hub/hisTimetable"
    params = {
        "KEY": NEIS_API_KEY, "Type": "json",
        "ATPT_OFCDC_SC_CODE": "R10",
        "SD_SCHUL_CODE": "8750188",
        "ALL_TI_YMD": target_date,
        "GRADE": grade,
        "CLASS_NM": class_nm
    }
    try:
        res = requests.get(url, params=params).json()
        if "hisTimetable" in res:
            rows = res['hisTimetable'][1]['row']
            
            # 중요: 가져온 데이터 중 정확히 해당 학년과 반인 것만 필터링 (숫자/문자 타입 대응)
            filtered_rows = [
                r for r in rows 
                if str(r['GRADE']) == str(grade) and str(r['CLASS_NM']) == str(class_nm)
            ]
            
            if not filtered_rows:
                return f"{grade}학년 {class_nm}반의 시간표 정보가 없습니다."

            # 교시 순서대로 정렬
            filtered_rows.sort(key=lambda x: int(x['PERIO']))
            
            table_result = f"[{grade}학년 {class_nm}반 시간표]\n"
            for r in filtered_rows:
                table_result += f"{r['PERIO']}교시: {r['ITRT_CNTNT']}\n"
            return table_result
        
        return f"{grade}학년 {class_nm}반의 시간표 정보가 없습니다."
    except:
        return "시간표 서버 연결 실패"

# --- 3. 웹 화면 구성 ---
st.set_page_config(page_title="영광고 AI 비서", page_icon="🏫", layout="centered")

with st.sidebar:
    st.header("🏫 영광고 AI 가이드")
    st.info("오늘/내일 급식, 일정, 시간표를 물어보세요!")
    st.write("예: '내일 점심 뭐야?', '기말고사 언제야?', '1학년 1반 내일 시간표 알려줘'")

st.title("🏫 영광고등학교 AI 비서")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 질문 처리 및 답변 생성 ---
if prompt := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("영광고 실시간 데이터를 조회 중입니다..."):
            # 날짜 계산
            now = datetime.now()
            target_date = now
            if "내일" in prompt:
                target_date = now + timedelta(days=1)
            elif "어제" in prompt:
                target_date = now - timedelta(days=1)
            
            target_date_str = target_date.strftime("%Y%m%d")
            display_date = target_date.strftime("%Y년 %m월 %d일")

            # 학년/반 추출 로직
            # 기본값은 1학년 1반으로 설정하되 질문에 숫자가 있으면 업데이트
            target_grade = "1"
            target_class = "1"
            
            grade_find = re.search(r'(\d)학년', prompt)
            class_find = re.search(r'(\d+)반', prompt)
            
            if grade_find: target_grade = grade_find.group(1)
            if class_find: target_class = class_find.group(1)

            # 데이터 수집 (API 호출)
            meal_info = get_meal_by_day(target_date_str)
            # 학사일정 60일치 조회
            plan_info = get_school_plan(now.strftime("%Y%m%d"), (now + timedelta(days=60)).strftime("%Y%m%d"))
            timetable_info = get_timetable(target_date_str, target_grade, target_class)

            weekday_list = ["월", "화", "수", "목", "금", "토", "일"]
            current_weekday = weekday_list[target_date.weekday()]

            # 최종 프롬프트 생성
            full_prompt = f"""
            너는 영광고등학교 AI 도우미. 친절하고 학생들에게 도움이 되는 말투로 대답해줘.
            
            [조회 기준 정보]
            - 기준 날짜: {display_date}({current_weekday}요일)
            - 급식 정보: {meal_info}
            - 학사 일정: {plan_info}
            - 시간표 정보({target_grade}학년 {target_class}반): {timetable_info}
            
            [지침]
            1. 시간표 질문의 경우 반드시 "{target_grade}학년 {target_class}반" 기준임을 명시하고 보여줘.
            2. 학사일정 질문(시험, 방학 등)은 기준 날짜와 대조해서 D-Day를 알려주면 좋아.
            3. 만약 시간표나 급식 정보가 "정보가 없습니다"라면, 주말이거나 아직 학교에서 등록하지 않은 경우라고 설명해줘.
            
            질문: {prompt}
            """

            try:
                response = model.generate_content(full_prompt)
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")