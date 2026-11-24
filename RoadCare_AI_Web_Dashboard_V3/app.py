import json, io, base64, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from risk_ml import ranking, insights, forecast, grade
from cloud_link import settings,get,get_manifest


ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='RoadCare AI | Web V6',page_icon='🛣️',layout='wide')
st.markdown('''<style>.stApp{background:#F4F7FB;color:#17324D}section[data-testid="stSidebar"]{background:#102B49}section[data-testid="stSidebar"] *{color:#f5f8fc!important}div[data-testid="stMetric"]{background:#fff;border:1px solid #e0eaf2;padding:13px;border-radius:12px}h1,h2,h3{color:#17324D}</style>''',unsafe_allow_html=True)

def default_json():return json.loads((ROOT/'data/results.json').read_text(encoding='utf8'))
def get_df(upload,path):
    if upload is None:return pd.read_csv(ROOT/path)
    return pd.read_csv(upload)
def get_json(upload):
    if upload is None:return default_json()
    return json.load(upload)
def download(label,df,name):st.download_button(label,df.to_csv(index=False).encode('utf-8-sig'),name,mime='text/csv')
def plot(fig):st.plotly_chart(fig,use_container_width=True)
def source_tag(label):st.caption('데이터 출처: '+label)
def video_data(upload,path):
    if upload is None:return (ROOT/path).read_bytes()
    return upload.getvalue()
def player_html(left, right):
    """Show entire source frames (portrait or landscape) without cropping."""
    def uri(data):
        return 'data:video/mp4;base64,' + base64.b64encode(data).decode('ascii')
    html = r"""
<!doctype html><html lang="ko"><head><meta charset="utf-8"/>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;color:#17324D;background:transparent}
.video-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:start}
.video-panel{min-width:0}.video-panel b{display:block;margin:0 0 7px}
video{display:block;width:100%;height:auto;max-height:78vh;object-fit:contain;background:#101820;border-radius:10px}
.actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 6px}
button{padding:8px 12px;background:#087F87;color:white;border:0;border-radius:7px;cursor:pointer}
.note{font-size:12px;color:#52657C;line-height:1.5}
@media(max-width:620px){.video-grid{grid-template-columns:minmax(0,1fr)}video{max-height:72vh}}
</style></head><body>
<div class="video-grid">
 <div class="video-panel"><b>원본 영상</b><video id="a" controls autoplay loop muted playsinline preload="metadata" src="__LEFT__"></video></div>
 <div class="video-panel"><b>탐지 결과 영상</b><video id="b" controls autoplay loop muted playsinline preload="metadata" src="__RIGHT__"></video></div>
</div>
<div class="actions"><button onclick="playBoth()">▶ 동시 재생</button><button onclick="pauseBoth()">⏸ 일시정지</button><button onclick="restartBoth()">↺ 처음부터</button></div>
<div class="note">9:16 세로 영상과 16:9 가로 영상을 원본 비율로 표시합니다. 서로 다른 비율도 각각 유지하며, 브라우저 자동재생 정책에 따라 재생 버튼이 필요할 수 있습니다.</div>
<script>
const a=document.getElementById('a'),b=document.getElementById('b');
function playBoth(){b.currentTime=a.currentTime;a.play().catch(()=>{});b.play().catch(()=>{});}
function pauseBoth(){a.pause();b.pause();}
function restartBoth(){a.currentTime=0;b.currentTime=0;playBoth();}
a.addEventListener('seeked',()=>{if(Math.abs(a.currentTime-b.currentTime)>.7)b.currentTime=a.currentTime});
a.addEventListener('play',()=>{if(b.paused)b.play().catch(()=>{})});
function fitFrame(){
  const h=Math.ceil(document.documentElement.scrollHeight+8);
  window.parent.postMessage({isStreamlitMessage:true,type:'streamlit:setFrameHeight',height:h},'*');
}
for(const v of [a,b]){for(const event of ['loadedmetadata','loadeddata','resize','error'])v.addEventListener(event,fitFrame)}
window.addEventListener('resize',fitFrame);
new ResizeObserver(fitFrame).observe(document.body);
fitFrame();
</script></body></html>
"""
    html = html.replace('__LEFT__', uri(left)).replace('__RIGHT__', uri(right))
    import streamlit.components.v1 as components
    components.html(html, height=420, scrolling=False)


st.title('🛣️ RoadCare AI | Web V6')
st.caption('Supabase 자동 연동 · 실제 모델 결과 조회')
slots=['model_1','model_2','model_3']
@st.fragment(run_every=5)
def watch_catalog():
    if not settings():
        st.error('Supabase 연결 설정 없음'); return
    try:
        catalog=json.loads(get('sync/catalog_v6.json'))
        if not isinstance(catalog,list): raise ValueError('영상 목록 형식 오류')
        old=st.session_state.get('catalog',[])
        st.session_state.catalog=catalog
        if old!=catalog: st.rerun()
        st.caption('자동 동기화: 5초 간격 · 연결 정상')
    except Exception as e:
        st.warning('영상 목록 조회 실패: '+str(e))
watch_catalog()
records=st.session_state.get('catalog',[])
ids=[r['id'] for r in records]
if st.session_state.get('video_choice') not in ids:
    st.session_state.video_choice=ids[0] if ids else None
chosen=st.selectbox('영상 선택',ids,key='video_choice',format_func=lambda x:next(r['name'] for r in records if r['id']==x)) if ids else None
rec=next((r for r in records if r['id']==chosen),None)
if records: st.dataframe([dict(영상=r['name'],**{m:r.get('models',{}).get(m,'미등록') for m in slots}) for r in records],hide_index=True)
model_id=st.session_state.get('model_choice','model_1')
seg=rec.get('segment','R-001') if rec else 'R-001'
@st.cache_data(ttl=300,max_entries=8,show_spinner=False)
def fetch_object(path): return get(path)
result={'data_type':'NO_RESULT','detections':[],'summary':{}}
cloud_org=cloud_det=None
if rec:
    prefix='runs/'+chosen
    try: cloud_org=fetch_object(prefix+'/original.mp4')
    except Exception as e: st.warning('원본 영상 조회 실패: '+str(e))
    if rec.get('models',{}).get(model_id)=='분석 완료':
        try:
            result=json.loads(fetch_object(prefix+'/'+model_id+'/results.json'))
            cloud_det=fetch_object(prefix+'/'+model_id+'/result.mp4')
        except Exception as e: st.warning('결과 전송 대기 또는 조회 실패: '+str(e))
if st.button('다시 불러오기'):
    fetch_object.clear(); st.rerun()
try:
    simulation=pd.read_csv(ROOT/'data/simulation.csv')
    required={'segment_id','month','pothole_count','avg_relative_area','max_relative_area','recurrence_count','traffic_volume','road_age_year','risk_score_before','risk_score_after'}
    if not required.issubset(simulation.columns):st.error('simulation.csv 필수 컬럼 누락: '+str(sorted(required-set(simulation.columns))));st.stop()
    info=json.loads((ROOT/'data/best_model_info.json').read_text(encoding='utf8')) if model_id=='model_1' else {}
    performance=pd.DataFrame([dict(model=info['model_name'],**{k:info.get(k) for k in ['precision','recall','f1','map50','map50_95','fps']})]) if info else pd.DataFrame()
    ranks=ranking(simulation);row=ranks.loc[ranks.segment_id==seg].iloc[0]
    detections=pd.DataFrame(result.get('detections',[]))
except Exception as e:st.error(f'데이터 로딩 오류: {e}');st.stop()
t1,t2,t3,t4,t5=st.tabs(['01 · AI 포트홀 영상 비교','02 · 도로 위험도·우선순위','03 · 월별 변화·보수효과','04 · Intelligent Insight','05 · AI 모델 성능'])
with t1:
    st.subheader('원본 영상 / 탐지 결과 영상')
    if cloud_org is not None and cloud_det is not None:
        player_html(cloud_org,cloud_det)
    elif cloud_org is not None:
        a,b=st.columns(2); a.video(cloud_org); b.info('선택 모델: '+rec.get('models',{}).get(model_id,'미등록'))
    else: st.info('조회 가능한 영상이 없습니다.')
    st.radio('AI 결과 모델 선택',slots,key='model_choice',horizontal=True,format_func=lambda m:'SSDLite-MobileNetV3-Large' if m=='model_1' else m+' / '+(rec.get('models',{}).get(m,'미등록') if rec else '미등록'))
    source_tag('results.json · '+str(result.get('data_type','출처 미상')))
    summary=result.get('summary',{})
    n=len(detections)
    conf=pd.to_numeric(detections.get('confidence',pd.Series(dtype=float)),errors='coerce')
    area=pd.to_numeric(detections.get('relative_area',pd.Series(dtype=float)),errors='coerce')
    cols=st.columns(4)
    for c,label,value in zip(cols,['Detection Events','평균 Confidence','최대 Confidence','고유 Track (제공값)'],[n,f'{conf.mean():.3f}' if conf.notna().any() else '미측정',f'{conf.max():.3f}' if conf.notna().any() else '미측정',summary.get('current_cycle_unique_count','미제공')]):c.metric(label,value)
    c1,c2,c3=st.columns(3)
    c1.metric('평균 Relative Area',f'{area.mean():.4f}' if area.notna().any() else '미측정')
    c2.metric('최대 Relative Area',f'{area.max():.4f}' if area.notna().any() else '미측정')
    c3.metric(f'{seg} Risk Score',f'{row.risk_score:.1f}')
    if not detections.empty:
        a,b,c=st.columns(3)
        with a:
            if conf.notna().any():plot(px.histogram(detections,x='confidence',nbins=15,title='Confidence 분포'))
        with b:
            if area.notna().any():plot(px.histogram(detections,x='relative_area',nbins=15,title='Relative Area 분포'))
        with c:
            if 'timestamp_sec' in detections:
                d=detections.copy();d['time_bin_sec']=(pd.to_numeric(d.timestamp_sec,errors='coerce')//2)*2
                plot(px.bar(d.groupby('time_bin_sec').size().reset_index(name='events'),x='time_bin_sec',y='events',title='영상시간별 탐지 이벤트 (2초 단위)'))
        with st.expander('탐지 상세 데이터'):st.dataframe(detections,use_container_width=True)
    st.caption('Relative Area는 영상 BBox 면적 비율이며 실제 면적/깊이가 아닙니다. Detection Events는 고유 포트홀 개수가 아닙니다.')
with t2:
    st.subheader('30개 도로구간 위험도 및 유지관리 우선순위')
    a,b,c,d=st.columns(4)
    for col,label,val in [(a,'Risk Score',f'{row.risk_score:.1f}/100'),(b,'위험등급',row.grade),(c,'현재 순위',f'{int(row["rank"])}/30'),(d,'포트홀 수 (시뮬레이션)',int(row.pothole_count))]:col.metric(label,val)
    advice={'관찰':'정기 모니터링','주의':'현장 상태 점검','우선 점검':'단기간 내 현장점검과 보수 검토','즉시 점검 권고':'우선 현장확인과 신속한 보수 검토'}
    st.info(f'{seg} 유지관리 권고: {advice[row.grade]}')
    a,b=st.columns([2,1])
    with a:st.dataframe(ranks[['rank','segment_id','risk_score','grade','pothole_count','recurrence_count','traffic_volume','road_age_year']],use_container_width=True,hide_index=True)
    with b:plot(px.bar(ranks.head(5).sort_values('risk_score'),x='risk_score',y='segment_id',orientation='h',title='위험도 Top 5'))
    download('30개 구간 순위 CSV',ranks,'segment_ranking.csv')
    source_tag('simulation.csv · 프로젝트용 위험도 지표 (공인 안전등급 아님)')
with t3:
    st.subheader('월별 변화 및 보수효과')
    agg=simulation.groupby('month',as_index=False).agg(pothole_count=('pothole_count','sum'),avg_relative_area=('avg_relative_area','mean'))
    monthly_risk=simulation.copy();monthly_risk['risk']=monthly_risk.apply(lambda r: __import__('risk_ml').risk(r),axis=1)
    danger=monthly_risk.assign(high=lambda d:d.risk>=60).groupby('month').high.sum().reset_index(name='risk_segments')
    agg=agg.merge(danger,on='month')
    a,b,c=st.columns(3)
    with a:plot(px.line(agg,x='month',y='pothole_count',markers=True,title='월별 포트홀 발생'))
    with b:plot(px.line(agg,x='month',y='avg_relative_area',markers=True,title='월별 평균 상대크기'))
    with c:plot(px.line(agg,x='month',y='risk_segments',markers=True,title='월별 우선점검 이상 구간'))
    sub=simulation[simulation.segment_id==seg].sort_values('month')
    a,b=st.columns(2)
    with a:plot(px.line(sub,x='month',y='pothole_count',markers=True,title=f'{seg} 최근 12개월'))
    with b:
        rec=simulation.groupby('segment_id',as_index=False).recurrence_count.sum().nlargest(5,'recurrence_count')
        plot(px.bar(rec,x='segment_id',y='recurrence_count',title='재발 집중구간 Top 5'))
    vals=sub.pothole_count.to_numpy()
    st.write('최근 1개월 증감률:',f'{(vals[-1]-vals[-2])/vals[-2]*100:+.1f}%' if len(vals)>1 and vals[-2]!=0 else '산정불가')
    st.write('최근 3개월 증감률:',f'{(vals[-1]-vals[-4])/vals[-4]*100:+.1f}%' if len(vals)>3 and vals[-4]!=0 else '산정불가')
    st.write('최근 6개월 추세:', '증가' if len(vals)>=6 and np.polyfit(np.arange(6),vals[-6:],1)[0]>0 else '감소 또는 유지' if len(vals)>=6 else '자료 부족')
    before=float(sub.iloc[-1].risk_score_before);after=float(sub.iloc[-1].risk_score_after)
    a,b,c=st.columns(3);a.metric('보수 전 Risk',f'{before:.1f}');b.metric('보수 후 Risk',f'{after:.1f}');c.metric('감소율',f'{(before-after)/before*100:.1f}%' if before else '산정불가')
    source_tag('simulation.csv · 가상 월별 데이터 (영상 기반 실제 탐지와 합산하지 않음)')
with t4:
    st.subheader('Intelligent Insight')
    st.caption('SIMULATION DATA 기반 탐색적 분석 · 실제 현장 위험 또는 예측 정확도 검증 아님')
    try:
        anomalies=insights(simulation)
        st.write('Isolation Forest 이상구간')
        st.dataframe(anomalies[['segment_id','anomaly_score','anomaly','pothole_count','recurrence_count']].sort_values('anomaly_score').head(12),hide_index=True,use_container_width=True)
        pred,mae=forecast(simulation)
        st.write('다음 달 포트홀 발생량 예측 · Random Forest')
        if not pred.empty:
            st.metric('선택 구간 다음 달 예상 발생량',f'{float(pred.loc[pred.segment_id==seg,"next_month_prediction"].iloc[0]):.1f}')
            st.caption(f'시뮬레이션 시간순 검증 MAE: {mae:.2f} (실제 현장 성능 아님)' if mae is not None else '검증 자료 부족')
            plot(px.bar(pred.nlargest(10,'next_month_prediction'),x='segment_id',y='next_month_prediction',title='예상 발생량 상위 10개 구간'))
        insight=anomalies[['segment_id','anomaly_score','anomaly']].merge(pred,on='segment_id',how='left')
        download('Intelligent Insight CSV',insight,'intelligent_insight.csv')
    except Exception as e:st.warning(f'ML 분석 불가: {e}')
with t5:
    st.subheader('AI 모델 성능 비교')
    if info:
        st.caption('제공된 학습 검증 기록 · 웹에서 재평가하지 않음')
        st.json(info)
        st.dataframe(performance,hide_index=True)
        download('모델 성능 CSV',performance,'model_performance.csv')
    else: st.info('선택 모델의 성능 정보가 아직 등록되지 않았습니다.')
with st.sidebar:
    st.caption('웹 조회 전용 · 위험도 및 월별 통계는 시뮬레이션 데이터')
    st.download_button('results.json',json.dumps(result,ensure_ascii=False,indent=2).encode(),file_name='results.json')
