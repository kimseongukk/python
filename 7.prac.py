import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px

st.title('종합 실습')
st.header('_2021 서울교통공사 지하철 월별 하차 인원_')

# streamlit//data_subway_in_seoul.csv
# encoding='cp949'  읽어오고 확인하기 
df = pd.read_csv('data_subway_in_seoul.csv', encoding = 'cp949')

# button을 누르면 원본데이터 주소가 나타남: https://www.data.go.kr/data/15044247/fileData.do
if st.button('data copyright link'):
    st.write('https://www.data.go.kr/data/15044247/fileData.do')

# checkbox를 선택하면 원본 데이터프레임이 나타남
if st.checkbox('원본 데이터 보기'):
    st.dataframe(df)

# '구분' 컬럼이 '하차'인 데이터를 선택
# 새로운 데이터 프레임-에 저장
df_off = df.loc[df['구분']=='하차']


st.subheader('전체 호선별 시간대별 하차 인원')    

# 불필요한 컬럼 '날짜','연번','역번호','역명','구분','합계' 제외
# 새로운 데이터 프레임-에 저장
df_line = df_off.drop(['날짜','연번','역번호','역명','구분','합계'], axis = 1)

# melt 함수 사용 unpivot: identifier-'호선', unpivot column-'시간', variable column-'인원수' 
# 새로운 데이터 프레임-에 저장
df_line_melted =  pd.melt(df_line, id_vars=['호선'], var_name='시간', value_name='인원수')

# '호선','시간' 별 인원수 집계 +.reset_index() & 확인
df_line_melted = df_line_melted.groupby(['호선','시간'])['인원수'].sum().reset_index()

# altair mark_line 차트 그리기
chart = alt.Chart(df_line_melted).mark_line().encode(
x='시간', y='인원수', color='호선').properties(width=650, height=350)  

st.dataframe(df_line_melted)
st.altair_chart(chart, use_container_width=True) 

st.subheader('선택 호선 시간대별 하차 인원')

# selectbox를 사용하여 '호선' 선택: 데이터프레임은 바로 이전에 사용한 최종 데이터프레임 사용
# .unique() 매소드를 사용하여 selectbox에 호선이 각각 하나만 나타나게 함
option = st.selectbox('호선 선택',df_line_melted['호선'].unique())

# .loc 함수를 사용하여 선택한 호선 데이터 선별하고
# 새로운 데이터 프레임-에 저장 & 확인
df_selected_line = df_line_melted.loc[df_line_melted['호선'] == option]
st.write(option, ' 데이터', df_selected_line)

# altair mark_area 차트 그리기
chart = alt.Chart(df_selected_line).mark_area().encode(x='시간', y='인원수', color=alt.value('pink')).properties(width=650, height=350)



# max_d = df_selected_line['인원수'].values.max()

text = alt.Chart(df_selected_line).mark_text(dx=0, dy=-7, color='black').encode(x='시간', y='인원수', text=alt.Text('인원수:Q'))

st.altair_chart(chart+text, use_container_width=True) 

st.subheader('선택역 시간대별 하차 인원')

# selectbox를 사용하여 '하차역' 선택: 데이터프레임은 '구분' 컬럼이 '하차'인 데이터프레임
# .unique() 매소드를 사용하여 selectbox에 하차역이 각각 하나만 나타나게 함
option = st.selectbox('하차역 선택',df_off['역명'].unique())

# .loc 함수를 사용하여 선택한 역의 데이터를 선별하고
# 새로운 데이터 프레임-에 저장 & 확인
df_sta = df_off.loc[df_off['역명']== option]


# 불필요한 컬럼 '연번','날짜','호선','역번호','역명','구분','합계' 제외하고 기존 데이터 프레임에 저장
df_sta = df_sta.drop(['연번','날짜','호선','역번호','역명','구분','합계'], axis = 1)


# # melt 함수 사용 unpivot: identifier-'날짜', unpivot column-'시간', variable column-'인원수' 
# # 새로운 데이터 프레임-에 저장
df_sta_melted = pd.melt(df_sta, var_name='시간', value_name='인원수')

# # '시간' 별 인원수 집계 +.reset_index() & 확인
df_sta_melted = df_sta_melted.groupby(['시간'])['인원수'].sum().reset_index()
st.write(option, ' 데이터',df_sta_melted)
    
# # altair mark_bar 차트 + text 그리기- x='시간', y='인원수'
chart = alt.Chart(df_sta_melted).mark_bar().encode(x='시간', y='인원수', color=alt.value('pink'))

text = alt.Chart(df_sta_melted).mark_text(dx=0, dy=-7, color='black').encode(x='시간', y='인원수', text=alt.Text('인원수:Q'))

st.altair_chart(chart+text, use_container_width=True)

# 파일실행: File > New > Terminal(anaconda prompt) - streamlit run streamlit\7.prac.py