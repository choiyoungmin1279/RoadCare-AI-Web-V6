from pathlib import Path
import json
import pandas as pd
import streamlit as st
import plotly.express as px
from cloud_link import settings,get
from risk_ml import ranking,risk,insights,forecast
ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='RoadCare AI | Road Operations',page_icon='🛣️',layout='wide')
st.markdown('''<style>.block-container{max-width:1440px;padding-top:2rem} [data-testid="stMetric"]{background:#f4f7fc;border:1px solid #e0e8f4;border-radius:14px;padding:18px} h1,h2,h3{letter-spacing:-.035em} [data-testid="stHorizontalBlock"]{gap:1.2rem}</style>''',unsafe_allow_html=True)
MODELS={'model_1':'SSDLite','model_2':'YOLO11n','model_3':'RT-DETR'}
@st.cache_data(ttl=60,show_spinner=False,max_entries=16)
def fetch(path,scope):return get(path)
def read(path):return fetch(path,settings()[0:3:2])
def obj(path):return json.loads(read(path))
def download(df,name):st.download_button('CSV 다운로드',df.to_csv(index=False).encode('utf-8-sig'),name,key=name)
def chart(fig):st.plotly_chart(fig,use_container_width=True)
st.title('RoadCare AI')
st.caption('ROAD OPERATIONS CENTER  /  도로 유지관리 통합 모니터링')
a,b=st.columns([4,1]);a.write('클라우드 연결 설정: '+('설정됨' if settings() else '미설정'))
if b.button('데이터 새로고침'):fetch.clear()
catalog=[]; error=None
if settings():
 try:
  catalog=obj('sync/catalog_v6.json')
  if not isinstance(catalog,list):raise ValueError('목록 형식 오류')
 except Exception as e:catalog=[];error=str(e)
else:error='Streamlit Secrets에 Supabase 설정을 추가하세요.'
if error:st.warning('클라우드 목록 미수신: '+error)
else:st.success('클라우드 목록 수신 성공')
menu=st.radio('메뉴',['종합 현황','영상 분석 결과','도로 위험도','월별 통계','AI 지능형 분석','데이터 관리'],horizontal=True,label_visibility='collapsed')
sim=pd.read_csv(ROOT/'data/simulation.csv');sim['month']=sim.month.astype(str)
month=st.selectbox('통계 기준 월 (연습 데이터)',sorted(sim.month.unique(),reverse=True)) if menu in ['종합 현황','도로 위험도'] else sim.month.max()
ranks=ranking(sim,month)
infos={m:json.loads((ROOT/'model'/m/'best_model_info.json').read_text(encoding='utf8')) for m in MODELS}
if menu=='종합 현황':
 st.subheader('운영 현황'); cols=st.columns(4)
 for c,l,v in zip(cols,['등록 영상','분석 완료 (로컬 보고)','전송 완료 (로컬 보고)','모델 종류'],[len(catalog),sum(s=='분석 완료' for r in catalog for s in r.get('models',{}).values()),sum(s=='전송 완료' for r in catalog for s in r.get('transfers',{}).values()),3]):c.metric(l,v)
 st.subheader('우선 점검 구간 · 연습용 가상 데이터');chart(px.bar(ranks.head(5),x='segment_id',y='risk_score',color='grade'));st.dataframe(ranks.head(5)[['rank','segment_id','risk_score','grade']],hide_index=True)
elif menu=='영상 분석 결과':
 if not catalog:st.info('수신된 영상 목록이 없습니다.')
 else:
  r=st.selectbox('영상',catalog,format_func=lambda x:f"{x.get('name')} | {x.get('segment','미지정')} | {x['id'][:8]}")
  m=st.radio('AI 모델 선택',list(MODELS),format_func=MODELS.get,horizontal=True);prefix='runs/'+r['id'];path=prefix+'/'+m
  st.caption('로컬 보고 상태: '+str(r.get('models',{}).get(m,'미등록'))+' / '+str(r.get('transfers',{}).get(m,'전송 미확인')))
  try:
   result=obj(path+'/results.json');summary=result.get('summary',{});df=pd.DataFrame(result.get('detections',[]));conf=pd.to_numeric(df.get('confidence',pd.Series(dtype=float)),errors='coerce');st.success('선택 모델 결과 JSON 수신 성공')
   for c,l,v in zip(st.columns(4),['탐지 이벤트','추적 기반 개체 수','평균 신뢰도','추론 FPS'],[summary.get('cumulative_detection_events','—'),summary.get('current_cycle_unique_count','—'),f'{conf.mean():.1%}' if conf.notna().any() else '—',summary.get('inference_fps','—')]):c.metric(l,v)
   st.caption('탐지 이벤트 및 추적 개체 수는 실제 고유 포트홀 수와 다를 수 있습니다. 상대면적은 영상 내 BBox 비율입니다.')
   a,b=st.columns(2)
   for col,label,p in [(a,'원본 영상',prefix+'/original.mp4'),(b,MODELS[m]+' 분석 영상',path+'/result.mp4')]:
    with col:
     st.subheader(label)
     try:st.video(read(p))
     except Exception as e:st.warning('영상 수신 실패: '+str(e))
   st.write('처리 시간(초):',summary.get('processing_seconds','미측정'));st.dataframe(df,hide_index=True)
   st.download_button('결과 JSON',json.dumps(result,ensure_ascii=False,indent=2),'results.json')
   try:st.download_button('원본 탐지 CSV',read(path+'/detections.csv'),'detections.csv')
   except Exception as e:st.warning('CSV 미수신: '+str(e))
   try:st.json(obj(path+'/best_model_info.json'),expanded=False)
   except Exception as e:st.warning('모델 정보 미수신: '+str(e))
  except Exception as e:st.info('선택 모델 결과를 불러올 수 없습니다: '+str(e))
elif menu=='도로 위험도':
 st.subheader('도로구간 위험도 및 우선순위');st.warning('연습용 가상 데이터 · 실제 GPS 좌표가 없어 지리 지도 대신 구간 위험도 격자를 표시합니다.')
 prev=sorted(x for x in sim.month.unique() if x<month);ranks['rank_change']=ranks.segment_id.map(ranking(sim,prev[-1]).set_index('segment_id')['rank'])-ranks['rank'] if prev else None
 grid=ranks.sort_values('segment_id');chart(px.scatter(grid,x=[i%6 for i in range(len(grid))],y=[-(i//6) for i in range(len(grid))],color='grade',text='segment_id',hover_data=['risk_score']).update_traces(marker_size=30,textposition='bottom center').update_xaxes(visible=False).update_yaxes(visible=False))
 st.dataframe(ranks[['rank','segment_id','risk_score','grade','rank_change']],hide_index=True);download(ranks,'ranking.csv')
elif menu=='월별 통계':
 st.warning('연습용 가상 월별 데이터 · 실제 영상 탐지와 합산하지 않음');sim['risk']=sim.apply(risk,axis=1);agg=sim.groupby('month',as_index=False).agg(pothole_count=('pothole_count','sum'),risk=('risk','mean'));a,b=st.columns(2)
 with a:chart(px.line(agg,x='month',y='pothole_count',markers=True,title='월별 포트홀'))
 with b:chart(px.line(agg,x='month',y='risk',markers=True,title='평균 위험도'))
 seg=st.selectbox('도로 구간',sorted(sim.segment_id.unique()));sub=sim[sim.segment_id==seg];chart(px.line(sub,x='month',y=['risk_score_before','risk_score_after'],markers=True,title='보수 전후 위험도'));download(sub,'monthly.csv')
elif menu=='AI 지능형 분석':
 st.subheader('모델 성능 비교');st.caption('제공된 학습 평가 JSON 기준 · 동일 검증셋 재평가 아님')
 perf=pd.DataFrame([dict(model=MODELS[m],**{k:v.get(k) for k in ['precision','recall','f1','map50','map50_95','fps']}) for m,v in infos.items()]);st.dataframe(perf,hide_index=True);chart(px.bar(perf,x='model',y=['precision','recall','f1','map50','map50_95'],barmode='group'));download(perf,'performance.csv')
 st.subheader('Intelligent Insight');st.warning('가상 데이터 기반 탐색적 예측 · 실제 도로 안전 판단에 사용하지 마세요.')
 an=insights(sim);pred,mae=forecast(sim);st.dataframe(an[['segment_id','anomaly_score','anomaly']],hide_index=True)
 if not pred.empty:chart(px.bar(pred.nlargest(10,'next_month_prediction'),x='segment_id',y='next_month_prediction'));st.write('시간순 검증 MAE:',mae);download(pred,'forecast.csv')
else:
 st.subheader('클라우드 수신 목록');rows=[{'영상':r.get('name'),'구간':r.get('segment'),'모델':MODELS.get(m,m),'분석':s,'전송':r.get('transfers',{}).get(m,'미확인')} for r in catalog for m,s in r.get('models',{}).items()];df=pd.DataFrame(rows);st.dataframe(df,hide_index=True);download(df,'catalog.csv');st.caption('전송 상태는 로컬 보고값이며 실제 파일 수신은 영상 분석 메뉴에서 확인하세요.')
