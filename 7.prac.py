import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px

st.title('종합 실습')
st.header('_2021 서울교통공사 지하철 월별 하차 인원_')

# streamlit//data_subway_in_seoul.csv
# encoding='cp949'  읽어오고 확인하기 
df = 

# button을 누르면 원본데이터 주소가 나타남: https://www.data.go.kr/data/15044247/fileData.do
if 


# checkbox를 선택하면 원본 데이터프레임이 나타남
if


# '구분' 컬럼이 '하차'인 데이터를 선택
# 새로운 데이터 프레임-에 저장
df_off = 


st.subheader('전체 호선별 시간대별 하차 인원')    

# 불필요한 컬럼 '날짜','연번','역번호','역명','구분','합계' 제외
# 새로운 데이터 프레임-에 저장
df_line = df_off[

# melt 함수 사용 unpivot: identifier-'호선', unpivot column-'시간', variable column-'인원수' 
# 새로운 데이터 프레임-에 저장
df_line_melted = 


# '호선','시간' 별 인원수 집계 +.reset_index() & 확인
df_line_melted = 


# altair mark_line 차트 그리기
chart =    

st.

st.subheader('선택 호선 시간대별 하차 인원')

# selectbox를 사용하여 '호선' 선택: 데이터프레임은 바로 이전에 사용한 최종 데이터프레임 사용
# .unique() 매소드를 사용하여 selectbox에 호선이 각각 하나만 나타나게 함
option =                ,df_line_melted['호선'].unique())

# .loc 함수를 사용하여 선택한 호선 데이터 선별하고
# 새로운 데이터 프레임-에 저장 & 확인
df_selected_line = df_line_melted.
st.write(option, ' 데이터', df_selected_line)

# altair mark_area 차트 그리기
chart =         .mark_area().encode(
         x='', y='').properties(width=650, height=350)
st.

st.subheader('선택역 시간대별 하차 인원')

# selectbox를 사용하여 '하차역' 선택: 데이터프레임은 '구분' 컬럼이 '하차'인 데이터프레임
# .unique() 매소드를 사용하여 selectbox에 하차역이 각각 하나만 나타나게 함
option =                  df_off['역명'].unique())

# .loc 함수를 사용하여 선택한 역의 데이터를 선별하고
# 새로운 데이터 프레임-에 저장 & 확인
df_sta = df_off.

# 불필요한 컬럼 '연번','날짜','호선','역번호','역명','구분','합계' 제외하고 기존 데이터 프레임에 저장
df_sta = df_sta.

# melt 함수 사용 unpivot: identifier-'날짜', unpivot column-'시간', variable column-'인원수' 
# 새로운 데이터 프레임-에 저장
df_sta_melted = 

# '시간' 별 인원수 집계 +.reset_index() & 확인
df_sta_melted = 
st.write(option, ' 데이터',df_sta_melted)
    
# altair mark_bar 차트 + text 그리기- x='시간', y='인원수'
chart = 

text = 

st.


# 파일실행: File > New > Terminal(anaconda prompt) - streamlit run streamlit\7.prac.py