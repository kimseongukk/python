import pandas as pd
import numpy as np
import datetime
import joblib
from haversine import haversine
from urllib.parse import quote
import streamlit as st
from streamlit_folium import st_folium
import folium
import branca
from geopy.geocoders import Nominatim
import ssl
from urllib.request import urlopen
import plotly.express as px
import pickle
from folium import plugins
import json
import requests
import branca
import googlemaps
import polyline
import time
import urllib.request

def geocoding(address):
    geolocator = Nominatim(user_agent='eunho')
    location = geolocator.geocode(address)
    lati = location.latitude
    long = location.longitude
     
    return lati, long


# preprocessing : '발열', '고혈압', '저혈압' 조건에 따른 질병 전처리 함수(미션3 참고)
# 리턴 변수(중증질환,증상) : X, Y
def preprocessing(desease):
    
    desease['발열'] = new_x["체온"].map(lambda x:1 if x >= 37 else 0)
    desease['고혈압'] = new_x["수축기 혈압"].map(lambda x:1 if x >= 140 else 0)
    desease['저혈압'] = new_x["수축기 혈압"].map(lambda x:1 if x <= 90 else 0)

    Y = desease[["중증질환"]]
    X = desease[['체온', '수축기 혈압', '이완기 혈압', '호흡 곤란',
                 '간헐성 경련', '설사', '기침', '출혈', '통증', '만지면 아프다',
                 '무감각', '마비', '현기증', '졸도', '말이 어눌해졌다', '시력이 흐려짐',
                 '발열', '고혈압', '저혈압']]
                 

    return X, Y


# find_hospital : 실시간 병원 정보 API 데이터 가져오기 (미션1 참고)
# 리턴 변수(거리, 거리구분) : distance_df
def find_hospital(special_m, lati, long):
    
    context=ssl.create_default_context()
    context.set_ciphers("DEFAULT")
    
    key = "jbMloHktKBRTicjzz1JUQVaJ1j2MY%2Fyg2J764zZGrnn8i4D7q8ftgliJcERxZt8O8eyqnbv8vmTxdRmPUCNAbA%3D%3D"

    # city = 대구광역시, 인코딩 필요
    city = quote("대구광역시")

    # 미션1에서 저장한 병원정보 파일 불러오기 
    solution_df = pd.read_csv("https://raw.githubusercontent.com/euknow/Data/main/daegu_hospital_list(link).csv")

    # 응급실 실시간 가용병상 조회
    url_realtime = 'https://apis.data.go.kr/B552657/ErmctInfoInqireService/getEmrrmRltmUsefulSckbdInfoInqire'+'?serviceKey=' + key + '&STAGE1=' + city + '&pageNo=1&numOfRows=1000'
    result = urlopen(url_realtime, context=context)
    emrRealtime = pd.read_xml(result, xpath='.//item')
    solution_df = pd.merge(solution_df, emrRealtime[['hpid', 'hvec', 'hvoc']], on="hpid", how="inner")

    # 응급실 실시간 중증질환 수용 가능 여부
    url_acpt = 'https://apis.data.go.kr/B552657/ErmctInfoInqireService/getSrsillDissAceptncPosblInfoInqire' + '?serviceKey=' + key + '&STAGE1=' + city + '&pageNo=1&numOfRows=100'
    result = urlopen(url_acpt, context=context)
    emrAcpt = pd.read_xml(result, xpath='.//item')
    emrAcpt = emrAcpt.rename(columns={"dutyName":"hpid"})
    solution_df = pd.merge(solution_df,
                           emrAcpt[['hpid', 'MKioskTy1', 'MKioskTy2', 'MKioskTy3', 'MKioskTy4', 'MKioskTy5', 'MKioskTy7',
                                'MKioskTy8', 'MKioskTy9', 'MKioskTy10', 'MKioskTy11']])
                  
    # 컬럼명 변경
    column_change = {'hpid': '병원코드',
                     'dutyName': '병원명',
                     'dutyAddr': '주소',
                     'dutyTel3': '응급연락처',
                     'wgs84Lat': '위도',
                     'wgs84Lon': '경도',
                     'hperyn': '응급실수',
                     'hpopyn': '수술실수',
                     'hvec': '가용응급실수',
                     'hvoc': '가용수술실수',
                     'MKioskTy1': '뇌출혈',
                     'MKioskTy2': '뇌경색',
                     'MKioskTy3': '심근경색',
                     'MKioskTy4': '복부손상',
                     'MKioskTy5': '사지접합',
                     'MKioskTy7': '응급투석',
                     'MKioskTy8': '조산산모',
                     'MKioskTy10': '신생아',
                     'MKioskTy11': '중증화상'
                     }
    solution_df = solution_df.rename(columns=column_change)
    solution_df = solution_df.replace({"정보미제공": "N"})

    # 응급실 가용율, 포화도 추가
    
    solution_df.loc[solution_df['가용응급실수'] < 0, '가용응급실수'] = 0
    solution_df.loc[solution_df['가용수술실수'] < 0, '가용수술실수'] = 0

    solution_df['응급실가용율'] =  solution_df["가용응급실수"]/solution_df["응급실수"]
    solution_df.loc[solution_df['응급실가용율'] > 1,'응급실가용율']=1
    labels = ['불가', '혼잡', '보통', '원활']
    solution_df['응급실포화도'] = pd.cut(solution_df["응급실가용율"]*100, [-1,10,30,60,101], labels=labels)

    ### 중증 질환 수용 가능한 병원 추출
    ### 미션1 상황에 따른 병원 데이터 추출하기 참고

    if special_m == "중증 아님":
        condition1 = solution_df["응급실포화도"]!="불가"
        distance_df = solution_df[condition1]
    else:
        condition1 = (solution_df[special_m] == 'Y') & (solution_df["가용수술실수"] > 1)
        condition2 = solution_df["응급실포화도"]!="불가"
        distance_df = solution_df[condition1 & condition2]

    ### 환자 위치로부터의 거리 계산
    patient = (lati, long)
    distance = [haversine(patient, j[["위도", "경도"]], unit = 'km') for _,j in distance_df.iterrows()]
    
    
#     for idx, row in distance_df.iterrows():
#         distance.append(round(haversine((row['위도'], row['경도']), patient, unit='km'), 2))
    
    ls = ['2km이내', '5km이내', '10km이내', '10km이상']
    dis = [0,2,5,10, np.inf]
    distance_df['거리'] = distance
    distance_df['거리구분'] = pd.cut(distance_df["거리"], dis, labels=ls) 
                              
    return distance_df









# -------------------------------------------------병원 조회
# 레이아웃 구성하기 


st.set_page_config(
    page_icon="🌐",
    page_title="Map",
    layout="wide",
)

with st.expander(" ", expanded=True):
    st.image("https://user-images.githubusercontent.com/105876194/233120116-7aa68afc-46b6-42f2-add8-37cf3f9c4466.png")

st.markdown("## 근처 병원 조회")
st.markdown("#### 병명")
mkiosk = st.radio("질환 선택", ["중증 아님", "뇌출혈", "뇌경색", "복부손상", "심근경색", '신생아', '중증화상', '사지접합',  "응급투석", "조산산모"],horizontal=True)

symp = mkiosk
    
st.markdown("#### 현재 위치")
loc = st.text_input("현재 위치", label_visibility="collapsed")
st.markdown("#### 병원 조회")
with st.form(key="tab1_first"):
    if st.form_submit_button(label="조회"):
        lati, long = geocoding(loc)
        hospital_list = find_hospital(symp, lati, long)
        
        
        
        #### 필요 병원 정보 추출 
        display_column = ['병원명', "주소", "응급연락처", "응급실수", "수술실수", "가용응급실수", "가용수술실수", '응급실포화도', '거리', '거리구분', "위도", "경도","link"]
        display_df = hospital_list[display_column].sort_values(['거리구분', '응급실포화도', '거리'], ascending=[True, False, True])
        display_df.reset_index(drop=True, inplace=True)
        
        #### 추출 병원 지도에 표시
        patient = [lati, long]
        with st.expander("인근 병원 리스트", expanded=True):
            st.dataframe(display_df)
            
            api_key = "AIzaSyAZKxDQin4js8zyCz2gZNAFpFjD8GhhcwQ" # 발급받은 API 키 입력
            gmaps = googlemaps.Client(key=api_key)
            

            ll = list(zip(list(display_df['위도']), list(display_df['경도'])))

            # 지도 중심 설정
            m = folium.Map(location=[lati, long], tiles="cartodbpositron", zoom_start=11)
            
            distances = []
            for i in ll:
                origin = (lati, long)
                destination = i

                # 경로 검색
                now = datetime.datetime.now()
                directions_result = gmaps.directions(origin,destination, mode="transit", departure_time=now)

                distance = directions_result[0]['legs'][0]['distance']['text']
                distances.append(distance)

                # start_cress = directions_result[0]['legs'][0]['start_address']
                # end_address = directions_result[0]['legs'][0]['end_address']

                polyline_str = directions_result[0]['overview_polyline']['points']
                decoded_polyline = polyline.decode(polyline_str)

                # 출발지와 도착지를 마커로 표시
                # folium.Marker(location=[lati, long], icon=folium.Icon(color='green') ).add_to(m)
                # folium.Marker(location=destination, icon=folium.Icon(color='red')).add_to(m)
                
                plugins.AntPath(locations=decoded_polyline, reverse=False, dash_array=[20, 20]).add_to(m)
            
            tooltip = "Patient!"
            pat_icon = folium.Icon(color="red")
            pati=f"""
                    <h4>Patient Loc!</h4><br>
                    <p>
                    Lati : {patient[0]}
                    </p>
                    <p>
                    Long : {patient[1]}
                """
            
            
            # f"<b>Patient Location!\tLat: {patient[0]}\nLon: {patient[1]}</b>"
            folium.Marker(
                patient,
                popup=pati,
                icon=pat_icon,
                tooltip=tooltip).add_to(m)
            
            hp_locs = []
            for i, row in display_df.iterrows():
                hp_loc = list(row[["위도","경도"]].values)
                dis = row["거리"]
                name = row["병원명"]
                hp_locs.append(hp_loc)
                icon_hos = plugins.BeautifyIcon(
                    icon="star",
                    border_color="blue",
                    text_color="blue",
                    icon_shape="circle")
                    
                    # plugins.AntPath(
                    # locations=[patient, hp_loc],
                    # reverse=False, # 방향 True 위에서 아래, False 아래에서 위dash_array=[20, 20]).add_to(m)
                
                html = """<!DOCTYPE html>
                        <html>
                            <table style="height: 126px; width: 330px;">  <tbody> <tr>
                            <td style="background-color: #2A799C;"><div style="color: #ffffff;text-align:center;">병원명</div></td>
                            <td style="width: 200px;background-color: #C5DCE7;">{}</td>""".format(row['병원명']) + """ </tr> 
                            <tr><td style="background-color: #2A799C;"><div style="color: #ffffff;text-align:center;">가용응급실수</div></td>
                            <td style="width: 200px;background-color: #C5DCE7;">{}</td>""".format(row['가용응급실수']) + """</tr>
                            <tr><td style="background-color: #2A799C;"><div style="color: #ffffff;text-align:center;">거리(km)</div></td>
                            <td style="width: 200px;background-color: #C5DCE7;">{:.2f}</td>""".format(row['거리']) + """ </tr>                            
                            <a href={} target=_blank>Homepage Link!</a>""".format(row['link']) + """ 
                        </tbody> </table> </html> """
                
                iframe = branca.element.IFrame(html=html, width=350, height=150)
                popup_text = folium.Popup(iframe, parse_html=True)
                # hos_icon = folium.Icon(color="blue")
                
                folium.Marker(location=[row['위도'], row['경도']],
                              popup=popup_text, tooltip=row['병원명'], icon=icon_hos).add_to(m)
                
 
            st_folium(m, width=1000)
            # navi = st.text_input("Where do you want to go?")
                
                                
                
                

        