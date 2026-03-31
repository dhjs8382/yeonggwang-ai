import streamlit as st
import google.generativeai as genai
import requests
from datetime import datetime, timedelta

# --- 1. 설정 (본인의 API 키를 입력하세요) ---
GOOGLE_API_KEY = "AIzaSyAoLO0yzG17rD3kvW2hK0-LDa2_MMh_scg" 
NEIS_API_KEY = "73119f2bf3604e4e9119d629b367ead7"

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

# --- 2. 수동 입력 학사일정 데이터 (1, 2학기 통합) ---
SCHOOL_PLAN = """
[영광고등학교 1학기 주요 학사일정]
- 3월 1일: 3.1절
- 3월 3일: 입학식
- 3월 17일: 기초학력 진단평가(1, 2학년)
- 3월 19일: 학교설명회
- 3월 24일: 전국연합모의고사(1, 2, 3학년)
- 3월 30일: 재량휴업일
- 4월 3일 ~ 4월 5일: 도민체전
- 4월 7일: 영어듣기평가(1학년)
- 4월 8일: 영어듣기평가(2학년)
- 4월 9일: 영어듣기평가(3학년)
- 4월 10일: 개인체력평가(PAPS)
- 4월 28일 ~ 5월 1일: 1학기 중간고사
- 5월 7일: 전국연합고사(3학년)
- 5월 14일: 현장체험학습
- 5월 15일: 한마음 체육축전
- 5월 20일: 수학소프트웨어 활용대회
- 5월 21일: 진로체험(1, 2학년)
- 5월 24일: 부처님오신날
- 5월 25일: 부처님오신날(대체휴일)
- 5월 26일 ~ 29일: 국제교류
- 6월 3일: 지방선거일
- 6월 4일: 대입수능모의평가(3학년)
- 6월 4일: 전국연합모의고사(1, 2학년)
- 6월 6일: 현충일
- 6월 29일 ~ 7월 2일: 1학기 기말고사
- 7월 8일: 전국연합고사(3학년)
- 7월 14일: 감성문학제
- 7월 15일: 빅데이터를 활용 프로젝트
- 7월 16일 ~ 17일: 해커톤대회
- 7월 21일: 방학식
- 8월 15일: 광복절
- 8월 17일: 광복절(대체휴일)
- 8월 18일: 개학일
- 8월 27일: 경북모의평가(3학년)

[영광고등학교 2학기 주요 학사일정]
- 9월 2일: 대입수능모의평가(3학년)
- 9월 2일: 전국연합고사(1, 2학년)
- 9월 8일: 영어듣기평가(1학년)
- 9월 9일: 영어듣기평가(2학년)
- 9월 10일: 영어듣기평가(3학년)
- 9월 18일: 2학기 중간(1, 2학년)
- 9월 18일: 2학기 기말고사(3학년)
- 9월 21일: 2학기 기말고사(3학년)
- 9월 21일: 2학기 중간(1, 2학년)
- 9월 22일: 2학기 기말고사(3학년)
- 9월 22일: 2학기 중간(1, 2학년)
- 9월 23일: 2학기 기말고사(3학년)
- 9월 23일: 2학기 중간(1, 2학년)
- 9월 24일: 추석연휴
- 9월 25일: 추석
- 9월 26일: 추석연휴
- 10월 3일: 개천절
- 10월 7일: 학부모초청 공개수업의 날
- 10월 9일: 한글날
- 10월 12일 ~ 14일: 1학년 야영
- 10월 12일 ~ 15일: 2학년 수학여행
- 10월 20일: 전국연합고사(1, 2, 3학년)
- 10월 28일: 경북모의평가(2학년)
- 10월 30일: 경제수학 과학캠프(예술제)
- 11월 4일: 영어신문제작 프로젝트
- 11월 18일: 수능 예비소집일
- 11월 19일: 대학수학능력시험일
- 11월 20일: 재량휴업일
- 12월 15일 ~ 12월 18일: 2학기 기말고사(1,2학년)
- 12월 25일: 성탄절
- 1월 1일: 신정
- 1월 7일: 졸업식
- 1월 8일: 종업식
"""

# --- 3. 날짜별 급식 가져오기 함수 ---
def get_meal_by_day(target_date):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": NEIS_API_KEY, "Type": "json",
        "ATPT_OFCDC_SC_CODE": "R10", # 경북교육청
        "SD_SCHUL_CODE": "8750188",   # 영광고등학교
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
        return "해당 날짜의 급식 정보가 나이스에 등록되어 있지 않습니다."
    except:
        return "급식 서버 연결에 실패했습니다."

# --- 4. 웹 화면 구성 ---
st.set_page_config(page_title="영광고 AI 비서", page_icon="🏫", layout="centered")

# 사이드바 (정보창)
with st.sidebar:
    st.header("🏫 영광고 AI 가이드")
    st.info("오늘/내일 급식과 일정을 물어보세요!")
    st.write("예: '내일 점심 뭐야?', '기말고사 언제야?'")

st.title("🏫 영광고등학교 AI 비서 V2.5")
st.markdown("---")

# 세션 상태 초기화 (대화 기록)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. 질문 처리 로직 ---
if prompt := st.chat_input("질문을 입력하세요..."):
    # 사용자 질문 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("영광고 데이터를 분석 중입니다..."):
            # 날짜 계산 (오늘/내일/어제 판단)
            now = datetime.now()
            target_date_str = now.strftime("%Y%m%d")
            display_date = now.strftime("%Y년 %m월 %d일")
            
            if "내일" in prompt:
                target_date_str = (now + timedelta(days=1)).strftime("%Y%m%d")
                display_date = (now + timedelta(days=1)).strftime("%Y년 %m월 %d일")
            elif "어제" in prompt:
                target_date_str = (now - timedelta(days=1)).strftime("%Y%m%d")
                display_date = (now - timedelta(days=1)).strftime("%Y년 %m월 %d일")

            # 데이터 수집
            meal_info = get_meal_by_day(target_date_str)
            weekday_list = ["월", "화", "수", "목", "금", "토", "일"]
            today_weekday = weekday_list[now.weekday()]
            
            # AI에게 보낼 최종 프롬프트
            full_prompt = f"""
            너는 영광고등학교 AI 비서야.
            사용자가 묻는 시점의 오늘 날짜는 {now.strftime('%Y년 %m월 %d일')}({today_weekday}요일)이야.
            
            [조회된 급식 정보 ({display_date})]
            {meal_info}
            
            [수동 입력 학사일정]
            {SCHOOL_PLAN}
            
            [지침]
            1. 질문에 "내일"이 포함되면 위 급식 정보가 {display_date}의 것임을 인지하고 답변해줘.
            2. 학사일정 질문에는 날짜를 계산해서 "몇 일 남았다"는 식으로 친절하게 답해줘.
            3. 급식 메뉴 중 고기나 맛있는게 있다면 강조해줘.
            
            질문: {prompt}
            """
            
            try:
                response = model.generate_content(full_prompt)
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"AI 답변 생성 중 오류 발생: {e}")