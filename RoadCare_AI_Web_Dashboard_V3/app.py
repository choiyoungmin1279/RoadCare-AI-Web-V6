import json, io, base64, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from risk_ml import ranking, insights, forecast, grade
from cloud_link import settings,get,put,original_created_at

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='RoadCare AI | Web V12',page_icon='🛣️',layout='wide',initial_sidebar_state='expanded')
st.markdown("""<style>
.stApp{background:#eaf3f9;color:#102b43}.block-container{max-width:1900px;padding:1.4rem 1.5rem 2rem}.hero{background:linear-gradient(100deg,#f7fbff 0%,#e3f2f8 42%,#123e54 100%);color:#102b43;padding:18px 22px;border-radius:12px;display:flex;align-items:center;gap:20px;min-height:92px;overflow:hidden}.hero h1{color:#102b43!important;font-size:34px;margin:0;padding:0}.hero em{color:#087f87;font-style:normal}.hero span{color:#284b63;font-weight:600}.hero img{width:32%;height:76px;object-fit:cover;border-radius:8px;margin-left:auto}.hero .tag{color:white;font-size:12px;white-space:nowrap}h1,h2,h3{color:#102b43}[data-testid=stHeader]{background:transparent}[data-testid=stSidebar]{background:linear-gradient(155deg,#102b43,#0b354b 75%,#07556a);min-width:235px}[data-testid=stSidebar] *{color:#f0f8ff!important}[data-testid=stSidebar] [data-testid=stRadio] label{padding:12px 9px;border-radius:8px;cursor:pointer}[data-testid=stSidebar] [data-testid=stRadio] label:has(input:checked){background:#087eae}[data-testid=stSidebar] [data-testid=stRadio] [role=radiogroup]{gap:8px}[data-testid=stSidebar] button{background:#16475d;border-color:#42687b}[data-testid=stVerticalBlockBorderWrapper]{border:1px solid #d5e5ef!important;border-radius:13px!important;background:#fafdff;box-shadow:0 3px 10px #123e5410}[data-testid=stMetric]{background:#eaf3f9;border:1px solid #d8e6ef;border-radius:9px;padding:10px}[data-testid=stMetricValue]{color:#102b43;font-size:24px}[data-testid=stMetricLabel]{font-size:12px}.stButton button,.stDownloadButton button{border-radius:8px}button[kind=primary]{background:#087da7!important;border-color:#087da7!important;color:white!important}.listhead{background:#dcecf5;padding:7px;border-radius:6px;font-weight:700;font-size:12px}.status{font-size:12px;font-weight:700;padding:4px 7px;border-radius:12px;display:inline-block;white-space:normal}.stCaption{color:#52657c}.section-title{font-size:25px;font-weight:800;color:#102b43;margin:8px 0}.section-title small{font-size:13px;font-weight:400;color:#52657c;margin-left:12px}@media(max-width:700px){.hero{display:block;padding:12px}.hero h1{font-size:25px}.hero img,.hero .tag{display:none}.block-container{padding:1rem!important}}
</style>""",unsafe_allow_html=True)

def get_df(upload,path):
    return pd.read_csv(upload if upload is not None else ROOT/path)
def download(label,df,name):st.download_button(label,df.to_csv(index=False).encode('utf-8-sig'),name,mime='text/csv')
def plot(fig):st.plotly_chart(fig.update_layout(colorway=['#009fa5','#ff902d','#2563eb','#10213b','#e55353'],margin=dict(l=12,r=12,t=45,b=12),height=260,paper_bgcolor='#fafdff',plot_bgcolor='#fafdff'),use_container_width=True)
def source_tag(label):st.caption('데이터 출처: '+label)
def video_data(upload,path):
    if upload is None:return (ROOT/path).read_bytes()
    return upload.getvalue()
def player_html(left, right, mode="자동"):
    """Show entire source frames (portrait or landscape) without cropping."""
    def uri(data):
        return 'data:video/mp4;base64,' + base64.b64encode(data).decode('ascii') if data else ''
    html = r"""
<!doctype html><html lang="ko"><head><meta charset="utf-8"/>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;color:#17324D;background:transparent}
.video-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:start}
.video-panel{min-width:0}.video-panel b{display:block;margin:0;padding:10px 12px;background:#34576b;color:white;border-radius:8px 8px 0 0}.video-panel:nth-child(2) b{background:#087f91}
video{display:block;width:100%;aspect-ratio:16/9;height:auto;max-height:78vh;object-fit:contain;background:#101820;border-radius:0 0 8px 8px}
.actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 6px}
button{padding:8px 12px;background:#087F87;color:white;border:0;border-radius:7px;cursor:pointer}
.note{font-size:12px;color:#52657C;line-height:1.5}
@media(max-width:620px){.video-grid{grid-template-columns:minmax(0,1fr)}video{max-height:72vh}}
__MODE_CSS__</style></head><body>
<div class="video-grid">
 <div class="video-panel"><b>원본 영상</b><video id="a" controls autoplay loop muted playsinline preload="metadata" src="__LEFT__"></video></div>
 <div class="video-panel"><b>AI 분석 영상</b><video id="b" controls autoplay loop muted playsinline preload="metadata" src="__RIGHT__"></video><div id="pending" class="note"></div></div>
</div>
<div class="actions"><button onclick="playBoth()">▶ 동시 재생</button><button onclick="pauseBoth()">⏸ 일시정지</button><button onclick="restartBoth()">↺ 처음부터</button></div>
<div class="note">9:16 세로 영상과 16:9 가로 영상을 원본 비율로 표시합니다. 서로 다른 비율도 각각 유지하며, 브라우저 자동재생 정책에 따라 재생 버튼이 필요할 수 있습니다.</div>
<script>
const a=document.getElementById('a'),b=document.getElementById('b');
if(!a.getAttribute('src'))a.removeAttribute('src');
if(!b.getAttribute("src")){b.removeAttribute("src");document.getElementById("pending").textContent="분석 영상 전송 대기 / 결과 없음";}
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
    html = html.replace('__LEFT__', uri(left)).replace('__RIGHT__', uri(right)).replace('__MODE_CSS__', '.video-grid{grid-template-columns:1fr}' if mode=='모바일' else '.video-grid{grid-template-columns:repeat(2,minmax(0,1fr))}' if mode=='PC' else '')
    import streamlit.components.v1 as components
    components.html(html, height=420, scrolling=False)

@st.cache_data(ttl=45,max_entries=12,show_spinner=False)
def fetch(path,scope):return get(path)
def read(path):return fetch(path,settings()[0:3:2])
def obj(path):return json.loads(read(path))
slots=['model_1','model_2','model_3']
infos=json.loads((ROOT/'data/model_info.json').read_text(encoding='utf8'))
header_img=base64.b64encode((ROOT/'data/header_road.jpg').read_bytes()).decode('ascii')
st.markdown(f'<div class="hero"><div><h1>🛣 RoadCare <em>AI</em></h1><span>AI 도로 상태 분석 및 유지관리 플랫폼</span></div><img src="data:image/jpeg;base64,{header_img}" alt="도로"><div class="tag">클라우드 데이터 수신 · Web V12</div></div>',unsafe_allow_html=True)
from datetime import datetime, timezone
@st.fragment(run_every=2)
def catalog_watch():
    if not settings(): return
    try:
        current=json.loads(get('sync/catalog_v6.json'))
        if not isinstance(current,list): raise ValueError('목록 형식 오류')
        if current != st.session_state.get('catalog',[]):
            fetch.clear()
            st.session_state['catalog']=current
            st.rerun(scope='app')
        st.caption('목록 수신 정상 · 2초 주기 확인')
    except Exception:
        st.caption('목록 수신 대기 또는 연결 오류')
if st.sidebar.button('클라우드 데이터 새로고침',use_container_width=True):
    fetch.clear()
    if settings():
        try: st.session_state['catalog']=json.loads(get('sync/catalog_v6.json'))
        except Exception: st.warning('목록 수신 실패')
records=st.session_state.get('catalog',[])
if settings() and 'catalog' not in st.session_state:
    try:
        records=json.loads(get('sync/catalog_v6.json'))
        st.session_state['catalog']=records
    except Exception: pass
if not settings(): st.warning('Streamlit Cloud Secrets 설정 필요')
catalog_watch()
mode=st.sidebar.radio('화면 모드',['자동','PC','모바일'],horizontal=True,key='display_mode')
if mode=='모바일':
    st.markdown('<style>[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}[data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important} [data-testid="stExpander"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important} [data-testid="stExpander"] [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important} [data-testid="stExpander"] [data-testid="stColumn"]:first-child{flex:6 1 0!important}</style>',unsafe_allow_html=True)
elif mode=='자동':
    st.markdown('<style>@media(max-width:700px){[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}[data-testid="stColumn"]{min-width:100%!important;flex:1 1 100%!important} [data-testid="stExpander"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important} [data-testid="stExpander"] [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important} [data-testid="stExpander"] [data-testid="stColumn"]:first-child{flex:6 1 0!important}.block-container{padding:1rem!important}}</style>',unsafe_allow_html=True)
st.sidebar.markdown('## RoadCare AI')
st.sidebar.caption('도로 유지관리 · WEB')
page=st.sidebar.radio('화면 선택',['영상 분석','도로 위험도·우선순위','월별 변화·보수효과','Intelligent Insight','AI 모델 성능'],horizontal=False,label_visibility='collapsed',key='nav')
st.markdown('<div class="section-title">'+page+'<small>AI 도로 유지관리 플랫폼</small></div>',unsafe_allow_html=True)
model_id=st.segmented_control('AI 모델 (전체 화면 공통)',slots,format_func=lambda m:dict(zip(slots,['SSDLite','YOLO11n','RT-DETR']))[m],default=slots[0],key='model_choice') or slots[0]
ids=[r['id'] for r in records if 'id' in r]
@st.cache_data(ttl=10,show_spinner=False)
def alias_for(rid,scope):
    try:return json.loads(get('web_metadata/'+rid+'.json')).get('display_name','')
    except Exception:return ''
def display_name(r):return alias_for(r['id'],settings()[0:3:2]) or r.get('name',r['id']) if settings() else r.get('name',r['id'])
def status_label(r):
    status=r.get('models',{}).get(model_id,'대기 중')
    return {'분석 완료':'🟢 ✓ 분석 완료','분석 중':'🔄 분석 중','분석 실패':'🔴 ✕ 분석 실패'}.get(status,'⚪ '+status)
if ids and st.session_state.get('selected_run') not in ids:st.session_state['selected_run']=ids[0]

import html as html_lib
@st.cache_data(ttl=45,show_spinner=False,max_entries=100)
def row_summary(rid,mid,scope):
    try:
        data=json.loads(get(f'runs/{rid}/{mid}/results.json'))
        d=pd.DataFrame(data.get('detections',[]))
        return data.get('summary',{}).get('current_cycle_unique_count',len(d)), ', '.join(d['class_name'].astype(str).value_counts().index[:3]) if 'class_name' in d else '—'
    except Exception:return '—','—'
def list_panel():
    st.markdown('### 분석 영상 목록 (총 '+str(len(records))+'개)')
    if not records:st.caption('로컬 전송 대기');return
    widths=[.5,2.6,1.5,.8,1.4,1.1,1.7,.55,.55]
    for col,label in zip(st.columns(widths),['번호','영상 파일명','분석 상태','손상 개수','주요 손상','영상 길이','업로드 일시','수정','정보']):
        col.markdown('<div class="listhead">'+label+'</div>',unsafe_allow_html=True)
    for i,r in enumerate(records,1):
        rid=r['id']; name=display_name(r); status=r.get('models',{}).get(model_id,'대기 중')
        n,classes=row_summary(rid,model_id,settings()[0:3:2]) if status=='분석 완료' else ('—','—')
        duration,created=st.session_state.get('meta_'+rid+'_value',(r.get('duration','—'),r.get('created_at','—')))
        num,a,state,count,kind,length,date,b,c=st.columns(widths)
        num.write(i)
        if a.button('▶ '+name,key='pick_'+rid,use_container_width=True,type='primary' if rid==st.session_state.get('selected_run') else 'secondary'):
            st.session_state['selected_run']=rid;st.rerun()
        fg,bg={'분석 완료':('#087b38','#dcfce7'),'분석 중':('#1559c0','#dbeafe'),'분석 실패':('#b91c1c','#fee2e2')}.get(status,('#475569','#e2e8f0'))
        state.markdown(f'<span class="status" style="color:{fg};background:{bg}">{html_lib.escape(status_label(r))}</span>',unsafe_allow_html=True)
        count.write(str(n));kind.write(classes);length.write(str(duration));date.write(str(created))
        with b:
            with st.popover('✎',help='영상 이름 수정'):
                new=st.text_input('표시 이름',name,key='alias_'+rid,max_chars=150)
                if st.button('저장',key='save_'+rid,disabled=not new.strip()):
                    try:
                        put('web_metadata/'+rid+'.json',json.dumps({'display_name':new.strip()},ensure_ascii=False).encode(),'application/json');alias_for.clear();st.rerun()
                    except Exception:st.error('이름 저장 실패 · 연결 확인')
        with c:
            with st.popover('ⓘ',help='영상 정보'):
                st.write(name)
                if st.button('정보 조회',key='meta_'+rid):
                    try:
                        import tempfile, subprocess, imageio_ffmpeg,re
                        with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
                            f.write(read('runs/'+rid+'/original.mp4'));f.flush()
                            proc=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-i',f.name],capture_output=True,text=True,timeout=30)
                            match=re.search(r'Duration: (\d+:\d+:\d+(?:\.\d+)?)',proc.stderr)
                        duration=match.group(1).split('.')[0] if match else '확인 불가'
                    except Exception:duration='확인 불가'
                    try:created=original_created_at(rid)
                    except Exception:created='확인 불가'
                    st.session_state['meta_'+rid+'_value']=(duration,created)
                duration,created=st.session_state.get('meta_'+rid+'_value',('정보 조회 버튼을 눌러주세요','정보 조회 버튼을 눌러주세요'))
                st.write('총 영상 길이: '+duration);st.write('추가된 날짜: '+created)

chosen=st.session_state.get('selected_run') if ids else None
rec=next((r for r in records if r.get('id')==chosen),None)
seg=rec.get('segment','R-001') if rec else st.selectbox('도로 구간',[f'R-{i:03d}' for i in range(1,31)])
work='runs/'+chosen+'/'+model_id if chosen else None
ready=False;result={'data_type':'NO_RESULT','detections':[],'summary':{}}
if work and rec.get('models',{}).get(model_id)=='분석 완료':
    try:result=obj(work+'/results.json');ready=True
    except Exception:pass
sim=None
try:
    simulation=get_df(sim,'data/simulation.csv')
    required={'segment_id','month','pothole_count','avg_relative_area','max_relative_area','recurrence_count','traffic_volume','road_age_year','risk_score_before','risk_score_after'}
    if not required.issubset(simulation.columns):st.error('simulation.csv 필수 컬럼 누락: '+str(sorted(required-set(simulation.columns))));st.stop()
    performance=pd.DataFrame([dict(model=v['model_name'],**{k:v.get(k) for k in ['precision','recall','f1','map50','map50_95','fps']}) for v in infos.values()]);info=infos.get(model_id,{})
    ranks=ranking(simulation);seg=seg if seg in ranks.segment_id.values else str(ranks.iloc[0].segment_id);row=ranks.loc[ranks.segment_id==seg].iloc[0]
    detections=pd.DataFrame(result.get('detections',[]))
except Exception as e:st.error(f'데이터 로딩 오류: {e}');st.stop()

if page=='영상 분석':
    main,side=st.columns([2.15,1],gap='small')
    with main:
        st.markdown('### 원본 영상 / AI 분석 영상')
    if rec:
        with main:st.caption(display_name(rec)+' · '+status_label(rec))
    left=right=None
    if chosen:
        try:left=read('runs/'+chosen+'/original.mp4')
        except Exception:st.caption('원본 영상 수신 대기')
        if ready:
            try:right=read(work+'/result.mp4')
            except Exception:st.caption('분석 영상 수신 대기')
    with main:
        with st.container(border=True):player_html(left,right,mode)
    if not chosen:
        with main:st.info('로컬에서 전송된 영상이 없습니다.')
    @st.fragment(run_every=2)
    def live_panel(part):
        data=result if ready else None
        status=rec.get('models',{}).get(model_id,'대기 중') if rec else '대기 중'
        if work and (status=='분석 중' or (status=='분석 완료' and not ready)):
            try:
                candidate=json.loads(get(work+'/live.json'))
                if candidate.get('model')==model_id and candidate.get('status') in ('analyzing','complete'): data=candidate
            except Exception: st.caption('중간 데이터 수신 대기 또는 연결 오류')
        if part=='progress':
            st.markdown('**분석 진행률**')
            if data is not None and data.get('progress') is not None:st.progress(max(0.,min(1.,float(data['progress']))))
            elif ready:st.progress(1.)
            else:st.caption(status)
            return
        if part=='summary':st.markdown('### 분석 요약')
        st.caption(status+' · '+infos[model_id]['model_name'])
        if data is None:
            st.info('선택한 영상과 모델의 분석 데이터가 아직 없습니다.');return
        if data.get('progress') is not None: st.progress(max(0.,min(1.,float(data['progress']))))
        elif ready: st.progress(1.)
        st.caption('수신 확인: '+datetime.now(timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('Asia/Seoul')).strftime('%H:%M:%S')+' · 2초 주기 조회 (전송 지연 가능)')
        st.caption('실제 모델 데이터 · '+str(data.get('data_type','')))
        d=pd.DataFrame(data.get('detections',[])); summary=data.get('summary',{})
        conf=pd.to_numeric(d.get('confidence',pd.Series(dtype=float)),errors='coerce'); area=pd.to_numeric(d.get('relative_area',pd.Series(dtype=float)),errors='coerce')
        def fmt(x):return f'{x:.4f}' if pd.notna(x) else '—'
        if part=='summary':
            for col,(label,value) in zip(st.columns(2),[('누적 탐지 이벤트',summary.get('cumulative_detection_events','—')),('고유 Track',summary.get('current_cycle_unique_count','—'))]):col.metric(label,value)
            for col,(label,value) in zip(st.columns(2),[('평균 Confidence',fmt(conf.mean())),('최대 Confidence',fmt(conf.max()))]):col.metric(label,value)
            for col,(label,value) in zip(st.columns(3),[('평균 Relative Area',fmt(area.mean())),('최대 Relative Area',fmt(area.max())),('Risk Score · 가상 데이터',f'{row.risk_score:.1f}')]):col.metric(label,value)
            if 'class_name' in d and not d.empty:
                counts=d['class_name'].astype(str).value_counts().rename_axis('손상 유형').reset_index(name='Track')
                plot(px.pie(counts,names='손상 유형',values='Track',hole=.65,title='위험요소 비율'))
            return
        a,b,c=st.columns(3)
        with a:
            if conf.notna().any():plot(px.histogram(x=conf.dropna(),nbins=15,title='Confidence 분포'))
        with b:
            if area.notna().any():plot(px.histogram(x=area.dropna(),nbins=15,title='Relative Area 분포'))
        with c:
            if 'timestamp_sec' in d:
                bins=(pd.to_numeric(d.timestamp_sec,errors='coerce')//2)*2
                counts=bins.value_counts().sort_index().rename_axis('초').reset_index(name='신규 Track')
                plot(px.bar(counts,x='초',y='신규 Track',title='영상 시간별 신규 Track (2초)'))
        st.caption('Track별 최대 Confidence 및 상대 BBox 면적 기준. 실제 물리적 면적 또는 고유 포트홀 수가 아닙니다. 시간별 전체 이벤트는 V8에서 제공하지 않습니다.')
        with st.expander('탐지 상세 데이터'):st.dataframe(d,use_container_width=True)
    with side:
        with st.container(border=True):live_panel("summary")
    with st.container(border=True):live_panel("progress")
    with st.container(border=True):live_panel("charts")
    bottom,details=st.columns([3,1],gap='small')
    with bottom:
        with st.container(border=True):list_panel()
    with details:
        with st.container(border=True):
            st.markdown('### 영상 정보')
            if rec:
                st.write(display_name(rec))
                duration,created=st.session_state.get('meta_'+chosen+'_value',(rec.get('duration','—'),rec.get('created_at','—')))
                st.write('영상 길이: '+str(duration));st.write('업로드 일시: '+str(created))
                st.caption('목록의 정보 버튼에서 상세 조회')
            else:st.caption('선택된 영상 없음')
    if ready:
        st.write('실측 추론 FPS:',result.get('summary',{}).get('inference_fps','—'))
        st.download_button('결과 JSON',json.dumps(result,ensure_ascii=False).encode(),'results.json')
        for label,name in [('탐지 CSV','detections.csv'),('분석 영상','result.mp4')]:
            try:st.download_button(label,read(work+'/'+name),name)
            except Exception:st.caption(label+' 미수신')
if page=='도로 위험도·우선순위':
    st.subheader('30개 도로구간 위험도 및 유지관리 우선순위')
    st.warning('연습용 가상 데이터 · 실제 탐지 결과와 합산하지 않음')
    a,b,c,d=st.columns(4)
    for col,label,val in [(a,'Risk Score',f'{row.risk_score:.1f}/100'),(b,'위험등급',row.grade),(c,'현재 순위',f'{int(row["rank"])}/30'),(d,'포트홀 수 (시뮬레이션)',int(row.pothole_count))]:col.metric(label,val)
    advice={'관찰':'정기 모니터링','주의':'현장 상태 점검','우선 점검':'단기간 내 현장점검과 보수 검토','즉시 점검 권고':'우선 현장확인과 신속한 보수 검토'}
    st.info(f'{seg} 유지관리 권고: {advice[row.grade]}')
    a,b=st.columns([2,1])
    with a:st.dataframe(ranks[['rank','segment_id','risk_score','grade','pothole_count','recurrence_count','traffic_volume','road_age_year']],use_container_width=True,hide_index=True)
    with b:plot(px.bar(ranks.head(5).sort_values('risk_score'),x='risk_score',y='segment_id',orientation='h',title='위험도 Top 5'))
    download('30개 구간 순위 CSV',ranks,'segment_ranking.csv')
    source_tag('simulation.csv · 프로젝트용 위험도 지표 (공인 안전등급 아님)')
if page=='월별 변화·보수효과':
    st.subheader('월별 변화 및 보수효과')
    st.warning('연습용 가상 월별 데이터')
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
if page=='Intelligent Insight':
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
if page=='AI 모델 성능':
    st.subheader('AI 모델 성능 비교')
    st.caption('제공된 학습 결과 JSON 기준 · 독립 재평가 아님')
    a,b,c=st.columns(3)
    a.metric('Current Applied Model',str(info.get('model_name','미제공')))
    b.metric('Backbone',str(info.get('backbone','미제공')))
    c.metric('Best Epoch',str(info.get('best_epoch','미제공')))
    st.dataframe(performance,use_container_width=True,hide_index=True)
    a,b=st.columns(2)
    with a:plot(px.bar(performance,x='model',y=['precision','recall','f1','map50','map50_95'],barmode='group',title='제공된 검증 지표'))
    with b:plot(px.bar(performance,x='model',y='fps',title='제공된 FPS 비교'))
    st.write('선정 근거:',info.get('selection_reason','미제공'))
    download('모델 비교 CSV',performance,'model_performance.csv')
with st.expander('데이터 다운로드'):
    st.divider();st.subheader('데이터 다운로드')
    st.download_button('results.json',json.dumps(result,ensure_ascii=False,indent=2).encode(),file_name='results.json')
    download('simulation.csv',simulation,'simulation.csv')
    download('model_performance.csv',performance,'model_performance.csv')
