import json, io, base64, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from risk_ml import ranking, insights, forecast, grade
from cloud_link import settings,get,put,original_created_at

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='RoadCare AI | Web V24',page_icon='🛣️',layout='wide',initial_sidebar_state='expanded')
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
def player_html(left, right, mode="자동", detections=None, ready=False, playback_key=""):
    """Show entire source frames (portrait or landscape) without cropping."""
    def uri(data):
        return 'data:video/mp4;base64,' + base64.b64encode(data).decode('ascii') if data else ''
    rows=[]
    if detections is not None and 'timestamp_sec' in detections:
        seen=set()
        for i,r in enumerate(detections.to_dict('records')):
            try:
                t=float(r['timestamp_sec'])
                if not np.isfinite(t) or t<0:continue
            except (ValueError,TypeError):continue
            key=str(r.get('track_id',i))
            if key in seen:continue
            seen.add(key)
            def number(k):
                try:
                    v=float(r.get(k));return v if np.isfinite(v) else None
                except (ValueError,TypeError):return None
            rows.append([t,number('confidence'),number('relative_area')])
    rows.sort(key=lambda r:r[0])
    payload=json.dumps(rows,allow_nan=False)
    html = r"""
<!doctype html><html lang="ko"><head><meta charset="utf-8"/>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;color:#17324D;background:transparent}
.video-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:start}
.video-panel{min-width:0}.video-panel b{display:block;margin:0;padding:10px 12px;background:#34576b;color:white;border-radius:8px 8px 0 0}.video-panel:nth-child(2) b{background:#087f91}
video{display:block;width:100%;aspect-ratio:16/9;height:auto;max-height:300px;object-fit:contain;background:#101820;border-radius:0 0 8px 8px}
.actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:12px 0 6px}.mini-progress{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:12px;color:#34576b}.mini-progress progress{width:85px;height:9px;accent-color:#087f87}
button{padding:8px 12px;background:#087F87;color:white;border:0;border-radius:7px;cursor:pointer}
.note{font-size:12px;color:#52657C;line-height:1.5}
@media(max-width:620px){.video-grid{grid-template-columns:minmax(0,1fr)}video{max-height:220px}}
.timeline{margin-top:14px;border:1px solid #d5e5ef;border-radius:10px;padding:10px;background:#fafdff}.timeline-head{display:flex;justify-content:space-between;gap:8px;font-weight:bold;font-size:14px}.charts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:8px}.chart{min-width:0;border:1px solid #e1eaf0;border-radius:7px;padding:6px}.chart strong{font-size:12px}.chart svg{display:block;width:100%;height:110px}.timeline .note{margin-top:5px}@media(max-width:620px){.charts{grid-template-columns:1fr}} 
__MODE_CSS__</style></head><body>
<div class="video-grid">
 <div class="video-panel"><b>원본 영상</b><video id="a" controls loop muted playsinline preload="metadata" src="__LEFT__"></video></div>
 <div class="video-panel"><b>AI 분석 영상</b><video id="b" controls loop muted playsinline preload="metadata" src="__RIGHT__"></video><div id="pending" class="note"></div></div>
</div>
<div class="actions"><button onclick="playBoth()">▶ 동시 재생</button><button onclick="pauseBoth()">⏸ 일시정지</button><button onclick="restartBoth()">↺ 처음부터</button><div class="mini-progress">__PROGRESS__</div></div>

<section class="timeline"><div class="timeline-head"><span>영상 재생 연동 그래프</span><span id="clock">00:00</span></div><div class="charts" id="charts"></div><div class="note" id="chartnote">Track 최초 탐지 시간 기준 · Confidence / Relative Area는 Track별 최대값의 누적 평균 (프레임별 실측 변화 아님)</div></section>
<script>
const rows=__ROWS__;
const a=document.getElementById('a'),b=document.getElementById('b');
if(!a.getAttribute('src'))a.removeAttribute('src');
if(!b.getAttribute("src")){b.removeAttribute("src");document.getElementById("pending").textContent="분석 영상 전송 대기 / 결과 없음";}
const master=b.getAttribute('src')?b:a, other=master===b?a:b;
const available=v=>!!v.getAttribute('src');
const storageKey='roadcare-player-v23:'+__PLAYER_KEY__;
let saved=null;try{saved=JSON.parse(sessionStorage.getItem(storageKey));}catch(e){}
let wantsPlay=saved?.playing!==false, initialized=false, generation=0;
const videos=[a,b].filter(available);
function persist(){if(!initialized)return;try{sessionStorage.setItem(storageKey,JSON.stringify({playing:wantsPlay,time:master.currentTime||0,rate:master.playbackRate||1}));}catch(e){}}
function align(){if(available(other)&&Number.isFinite(other.duration)&&Math.abs(other.currentTime-master.currentTime)>.25)other.currentTime=Math.min(master.currentTime,other.duration);}
function applyPlayback(){const token=++generation;for(const v of videos){if(wantsPlay){if(v.paused)v.play().then(()=>{if(token!==generation&&!wantsPlay)v.pause();}).catch(()=>{});}else v.pause();}persist();}
function playBoth(){wantsPlay=true;align();applyPlayback();}
function pauseBoth(){wantsPlay=false;applyPlayback();draw();}
function restartBoth(){for(const v of videos)if(v.readyState)v.currentTime=0;draw();playBoth();}
for(const v of videos){
 v.addEventListener('play',()=>{if(!initialized||v.paused)return; if(!wantsPlay){wantsPlay=true;applyPlayback();}});
 v.addEventListener('pause',()=>{if(!initialized||!v.paused||v.ended)return;if(wantsPlay){wantsPlay=false;applyPlayback();}draw();});
 v.addEventListener('seeked',()=>{if(!initialized)return;const o=v===a?b:a;if(available(o)&&Number.isFinite(o.duration)&&Math.abs(o.currentTime-v.currentTime)>.25)o.currentTime=Math.min(v.currentTime,o.duration);persist();draw();});
 v.addEventListener('ratechange',()=>{if(!initialized)return;const o=v===a?b:a;if(available(o)&&o.playbackRate!==v.playbackRate)o.playbackRate=v.playbackRate;persist();});
}
function initPlayback(){if(initialized)return;if(videos.some(v=>!v.readyState&&!v.error))return;for(const v of videos){if(v.readyState&&saved){if(Number.isFinite(saved.time)&&Number.isFinite(v.duration))v.currentTime=Math.min(saved.time,v.duration);if(Number.isFinite(saved.rate)&&saved.rate>0)v.playbackRate=saved.rate;}}initialized=true;applyPlayback();draw();}
for(const v of videos){v.addEventListener('loadedmetadata',initPlayback);v.addEventListener('error',initPlayback);}
window.addEventListener('pagehide',persist);
const specs=[['누적 Track','#0891b2'],['Confidence · 누적 평균','#2563eb'],['Relative Area · 누적 평균','#d97706']];
const host=document.getElementById('charts');
for(const [name,color] of specs){const el=document.createElement('div');el.className='chart';el.innerHTML='<strong>'+name+'</strong><svg viewBox="0 0 240 110" role="img" aria-label="'+name+'"></svg>';host.appendChild(el);}
let last='';
function draw(){const t=available(master)?master.currentTime:0;const dur=Number.isFinite(master.duration)&&master.duration>0?master.duration:Math.max(1,rows.length?rows[rows.length-1][0]:1);const key=Math.floor(t*10)+'/'+dur;if(key===last)return;last=key;
 document.getElementById('clock').textContent=Math.floor(t/60)+':'+String(Math.floor(t%60)).padStart(2,'0');
 if(!rows.length)document.getElementById('chartnote').textContent='시간별 탐지 데이터 없음 또는 분석 결과 수신 대기';
 const points=[[],[],[]];let count=0,sums=[0,0],ns=[0,0];
 for(const r of rows){if(r[0]>t||r[0]>dur)break;count++;points[0].push([r[0],count]);for(let k=0;k<2;k++){if(r[k+1]!==null){sums[k]+=r[k+1];ns[k]++;points[k+1].push([r[0],sums[k]/ns[k]]);}}}
 points[0].unshift([0,0]);
 for(let k=0;k<3;k++){const max=k===0?Math.max(1,rows.length):1;const x=v=>32+Math.min(1,v/dur)*198,y=v=>85-Math.max(0,Math.min(1,v/max))*72;const pts=points[k];let markup='';for(let j=0;j<=2;j++){const yy=85-j*36;markup+=`<line x1="32" x2="230" y1="${yy}" y2="${yy}" stroke="#dbe5eb"/><text x="28" y="${yy+3}" text-anchor="end" font-size="9" fill="#52657c">${k===0?Math.round(max*j/2):(j/2).toFixed(1)}</text>`;}markup+=`<text x="32" y="101" font-size="9" fill="#52657c">0s</text><text x="230" y="101" text-anchor="end" font-size="9" fill="#52657c">${dur.toFixed(1)}s</text>`;if(pts.length){markup+=`<polyline points="${pts.map(p=>x(p[0])+','+y(p[1])).join(' ')}" fill="none" stroke="${specs[k][1]}" stroke-width="1.7"/>`;const stride=Math.max(1,Math.ceil(pts.length/150));for(let j=0;j<pts.length;j++){if(j%stride&&j!==pts.length-1)continue;markup+=`<circle cx="${x(pts[j][0])}" cy="${y(pts[j][1])}" r="2" fill="${specs[k][1]}"/>`;}}markup+=`<line x1="${x(t)}" x2="${x(t)}" y1="13" y2="85" stroke="#64748b" stroke-dasharray="3 3"/>`;host.children[k].querySelector('svg').innerHTML=markup;}
}
for(const event of ['timeupdate','seeked','loadedmetadata','ended','pause'])master.addEventListener(event,draw);
let lastSave=0;function tick(now){if(initialized&&wantsPlay&&!master.paused){align();draw();if(now-lastSave>250){persist();lastSave=now;}}requestAnimationFrame(tick);}draw();initPlayback();requestAnimationFrame(tick);
</script></body></html>
"""
    html = html.replace('__PLAYER_KEY__', json.dumps(hashlib.sha256(playback_key.encode()).hexdigest())).replace('__PROGRESS__', '분석 진행률 <progress value="100" max="100"></progress> 100%' if ready else '분석 진행률: 우측 분석 요약에서 실시간 확인').replace('__ROWS__', payload).replace('__LEFT__', uri(left)).replace('__RIGHT__', uri(right)).replace('__MODE_CSS__', '.video-grid{grid-template-columns:1fr}video{max-height:220px}.charts{grid-template-columns:1fr}' if mode=='모바일' else '.video-grid{grid-template-columns:repeat(2,minmax(0,1fr))}' if mode=='PC' else '')
    import streamlit.components.v1 as components
    # Explicit height prevents clipping; scrolling is a fallback on narrow screens.
    if mode=='자동':
        st.markdown('<style>@media(max-width:900px){iframe[title="st.iframe"]{height:1120px!important}}</style>',unsafe_allow_html=True)
    components.html(html, height=1120 if mode=='모바일' else 610, scrolling=True)

@st.cache_data(ttl=45,max_entries=12,show_spinner=False)
def fetch(path,scope):return get(path)
def read(path):return fetch(path,settings()[0:3:2])
def obj(path):return json.loads(read(path))
slots=['model_1','model_2','model_3']
legacy_infos=json.loads((ROOT/'data/model_info.json').read_text(encoding='utf8'))
def remote_registry():
    data=json.loads(get('sync/model_registry_v21.json'))
    if not isinstance(data,dict) or any(not isinstance(v,dict) for v in data.values()):raise ValueError('모델 목록 형식 오류')
    return {m:v for m,v in data.items() if str(v.get('model_name','')).strip().casefold()!='new road ai'}
header_img=base64.b64encode((ROOT/'data/header_road.jpg').read_bytes()).decode('ascii')
st.markdown(f'<div class="hero"><div><h1>🛣 RoadCare <em>AI</em></h1><span>AI 도로 상태 분석 및 유지관리 플랫폼</span></div><img src="data:image/jpeg;base64,{header_img}" alt="도로"><div class="tag">클라우드 데이터 수신 · Web V24</div></div>',unsafe_allow_html=True)
from datetime import datetime, timezone, timedelta
def fmt_stamp(value):
    if not value:return '기록 없음'
    try:
        dt=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone(timedelta(hours=9)))
        return dt.astimezone(timezone(timedelta(hours=9))).strftime('%Y.%m.%d %H:%M')
    except Exception:return str(value)
@st.fragment(run_every=2)
def catalog_watch():
    if not settings(): return
    current=st.session_state.get('catalog',[])
    registry_now=st.session_state.get('registry21')
    catalog_ok=registry_ok=False
    try:
        candidate=json.loads(get('sync/catalog_v6.json'))
        if isinstance(candidate,list):current=candidate;catalog_ok=True;st.session_state['last_catalog_ok']=datetime.now(timezone.utc).isoformat()
    except Exception:pass
    try:registry_now=remote_registry();registry_ok=True
    except Exception:pass
    if current != st.session_state.get('catalog',[]) or registry_now != st.session_state.get('registry21'):
        st.session_state['registry21']=registry_now
        st.session_state['catalog']=current
        fetch.clear()
        st.rerun(scope='app')
    st.caption(('● 목록 수신 정상' if catalog_ok else '● 목록 수신 실패 · 마지막 데이터 유지')+' · '+('모델 정보 수신 정상' if registry_ok else '모델 정보 수신 대기')+' · 마지막 갱신 '+fmt_stamp(st.session_state.get('last_catalog_ok'))+' KST · 2초 주기 확인')
if st.sidebar.button('클라우드 데이터 새로고침',use_container_width=True):
    fetch.clear()
    if settings():
        try: st.session_state['catalog']=json.loads(get('sync/catalog_v6.json'))
        except Exception: st.warning('목록 수신 실패')
        try: st.session_state['registry21']=remote_registry()
        except Exception: st.warning('모델 정보 수신 실패')
records=st.session_state.get('catalog',[])
if settings() and 'catalog' not in st.session_state:
    try:
        records=json.loads(get('sync/catalog_v6.json'))
        st.session_state['catalog']=records
    except Exception: pass
if not settings(): st.warning('Streamlit Cloud Secrets 설정 필요')
if settings() and st.session_state.get('registry21') is None:
    try:st.session_state['registry21']=remote_registry()
    except Exception:pass
infos=st.session_state.get('registry21')
if infos is None:infos=legacy_infos.copy()
else:infos=infos.copy()
for r in records:
    for m,status in r.get('models',{}).items():
        if status=='분석 완료' and m not in infos and m not in ('new_road_ai','NEW ROAD AI'):infos[m]={'model_name':m,'archived':True,'enabled':False}
slots=list(infos)
if not slots:
    infos={'no_model':{'model_name':'등록 모델 없음','enabled':False}};slots=list(infos)
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
if st.session_state.get('model_choice') not in slots:st.session_state['model_choice']=slots[0]
def model_label(m):
    v=infos[m];return str(v.get('model_name',m))+(' · 보관 결과' if v.get('archived') else ' · 비활성' if v.get('enabled') is False and m!='no_model' else '')
model_id=st.segmented_control('AI 모델 (전체 화면 공통)',slots,format_func=model_label,key='model_choice') or slots[0]
ids=[r['id'] for r in records if 'id' in r]
@st.cache_data(ttl=10,show_spinner=False)
def alias_for(rid,scope):
    try:return json.loads(get('web_metadata/'+rid+'.json')).get('display_name','')
    except Exception:return ''
def display_name(r):return alias_for(r['id'],settings()[0:3:2]) or r.get('name',r['id']) if settings() else r.get('name',r['id'])
def status_label(r):
    status=r.get('models',{}).get(model_id,'대기 중')
    return {'분석 완료':'🟢 ✓ 분석 완료','분석 중':'🔄 분석 중','분석 실패':'🔴 ✕ 분석 실패'}.get(status,'⚪ '+status)
def selectable(r):
    return r.get('models',{}).get(model_id)=='분석 완료' and r.get('transfers',{}).get(model_id,'전송 완료')=='전송 완료'
eligible=[r['id'] for r in records if selectable(r)]
if st.session_state.get('selected_run') not in eligible:st.session_state['selected_run']=eligible[0] if eligible else None

import html as html_lib
@st.cache_data(ttl=45,show_spinner=False,max_entries=100)
def row_summary(rid,mid,scope):
    try:
        data=json.loads(get(f'runs/{rid}/{mid}/results.json'))
        d=pd.DataFrame(data.get('detections',[]))
        return data.get('summary',{}).get('current_cycle_unique_count',len(d)), ', '.join(d['class_name'].astype(str).value_counts().index[:3]) if 'class_name' in d else '—'
    except Exception:return '—','—'
def select_video(rid, segment):
    # Widget callbacks run before the next script execution.
    st.session_state['selected_run'] = rid
    if segment in road_ids:
        st.session_state['v24_pending_segment'] = segment

CORE=('model_1','model_2','model_3')
def final_stamp(r):
    if not all(r.get('models',{}).get(m)=='분석 완료' for m in CORE):return None
    times=r.get('completed_at',{})
    try:return max(datetime.fromisoformat(times[m].replace('Z','+00:00')) for m in CORE).isoformat()
    except (KeyError,ValueError,TypeError):return None
@st.cache_data(ttl=600,show_spinner=False,max_entries=300)
def legacy_created(rid,scope):
    try:return original_created_at(rid)
    except Exception:return None
def created_stamp(r):
    return r.get('created_at') or (legacy_created(r['id'],settings()[0:3:2]) if settings() and r.get('cloud') else None)
def duration_label(r):
    try:
        n=int(float(r['duration_seconds']));return f'{n//3600:02d}:{n//60%60:02d}:{n%60:02d}'
    except (KeyError,ValueError,TypeError):return str(r.get('duration') or '—')
def date_cell(value):
    t=fmt_stamp(value)
    return html_lib.escape(t).replace(' ','<br>',1) if value else '—'
def row_state(r):return r.get('models',{}).get(model_id,'대기 중')
@st.fragment(run_every=2)
def list_panel():
    st.markdown("""<style>
    .st-key-v24list{background:#E8F1F7;border:1px solid #c4d4df;border-radius:12px;padding:13px;color:#102E45}
    .st-key-v24list [data-testid=stVerticalBlock]{gap:8px}
    .st-key-v24list [data-testid=stHorizontalBlock]{gap:8px;flex-wrap:nowrap!important}
    .st-key-v24list [data-testid=stColumn]{min-width:0!important;flex-basis:0!important}
    .st-key-v24list .v24head{background:#D7E8F1;border-radius:5px;padding:7px 3px;font-size:12px;font-weight:700;white-space:nowrap}
    .st-key-v24list .v24cell{font-size:12px;line-height:1.35;padding:7px 3px;color:#102E45}
    .st-key-v24list button{min-height:37px;border-radius:8px;font-size:13px;background:white;color:#102E45;border:1px solid #d0dce5}
    .st-key-v24list button[kind=primary]{background:#087DA1!important;color:white!important;border-color:#087DA1!important}
    .st-key-v24list button:disabled{background:#DFE7ED!important;color:#82919D!important}
    .st-key-v24list [class*=st-key-v24card] button{height:83px;text-align:left;white-space:pre-line;justify-content:flex-start;font-size:16px}
    .st-key-v24list [class*=st-key-v24card] button[kind=primary]{background:white!important;color:#245B80!important;border:2px solid #245B80!important}
    .st-key-v24list [class*=st-key-v24card] button p{white-space:pre-line}
    .st-key-v24list [data-testid=stPopover] button{padding:0;border:0;background:transparent}
    @media(max-width:850px){.st-key-v24list [class*=st-key-v24table]{overflow-x:auto}.st-key-v24list [class*=st-key-v24table] > div{min-width:680px}}
    </style>""",unsafe_allow_html=True)
    with st.container(key='v24list'):
        title,toggle=st.columns([5,1])
        title.markdown(f'### 분석 영상 목록 (총 {len(records)}개)')
        if toggle.button('펼치기' if st.session_state.get('v24collapsed') else '접기',key='v24toggle'):
            st.session_state['v24collapsed']=not st.session_state.get('v24collapsed',False);st.rerun(scope='fragment')
        if st.session_state.get('v24collapsed'):return
        if not records:st.caption('로컬 전송 대기');return
        filt=st.session_state.get('v24filter','전체')
        groups=[('전체','전체 영상','#245B80'),('분석 완료','분석 완료','#168653'),('분석 중','분석 중','#247AC1'),('분석 실패','분석 실패','#B42323')]
        for col,(k,label,color) in zip(st.columns(4),groups):
            n=sum(k=='전체' or row_state(r)==k for r in records)
            with col,st.container(key='v24card'+str(groups.index((k,label,color)))):
                st.markdown(f'<style>.st-key-v24card{groups.index((k,label,color))} button p{{color:{color}!important}}</style>',unsafe_allow_html=True)
                if st.button(f'{label}  \n{n}',key='v24filter'+k,type='primary' if filt==k else 'secondary',use_container_width=True):
                    st.session_state['v24filter']=k;st.rerun(scope='fragment')
        q=st.text_input('영상 이름 검색',placeholder='영상 이름 검색',label_visibility='collapsed',key='v24search')
        order=st.selectbox('정렬',['업로드 순','최신 등록 순','분석 완료 순','영상 이름순'],label_visibility='collapsed',key='v24sort')
        rows=[(r.get('registration_no',i),r,display_name(r)) for i,r in enumerate(records,1)]
        rows=[x for x in rows if (filt=='전체' or row_state(x[1])==filt) and q.casefold() in x[2].casefold()]
        if order=='최신 등록 순':rows.sort(key=lambda x:x[0],reverse=True)
        elif order=='분석 완료 순':rows.sort(key=lambda x:final_stamp(x[1]) or '',reverse=True)
        elif order=='영상 이름순':rows.sort(key=lambda x:x[2].casefold())
        else:rows.sort(key=lambda x:x[0])
        widths=[.42,2.6,.38,1.35,.85,1.4,1.4]
        with st.container(key='v24table'):
            for col,label in zip(st.columns(widths),['번호','영상 파일명','','분석 상태','영상 길이','업로드 일시','분석 일시']):col.markdown('<div class="v24head">'+(label or '&nbsp;')+'</div>',unsafe_allow_html=True)
            for num,r,name in rows:
                rid=r['id'];status=row_state(r);n=sum(r.get('models',{}).get(m)=='분석 완료' for m in CORE)
                cols=st.columns(widths)
                cols[0].markdown(f'<div class="v24cell">{num}</div>',unsafe_allow_html=True)
                if cols[1].button(('▸ ' if selectable(r) else '')+name,key='pick_'+rid,use_container_width=True,type='primary' if rid==st.session_state.get('selected_run') else 'secondary',disabled=not selectable(r),on_click=select_video,args=(rid,str(r.get('segment','R-001')))):
                    st.rerun(scope='app')
                with cols[2],st.popover('✎',help='영상 이름 수정'):
                    new=st.text_input('표시 이름',name,key='alias_'+rid,max_chars=150)
                    if st.button('저장',key='save_'+rid,disabled=not new.strip()):
                        try:put('web_metadata/'+rid+'.json',json.dumps({'display_name':new.strip()},ensure_ascii=False).encode(),'application/json');alias_for.clear();st.rerun(scope='app')
                        except Exception:st.error('이름 저장 실패 · 연결 확인')
                fg={'분석 완료':'#168653','분석 중':'#247AC1','분석 실패':'#B42323'}.get(status,'#788A9B')
                label=status
                if status=='분석 중':
                    try:
                        live=json.loads(get(f'runs/{rid}/{model_id}/live.json'))
                        if live.get('status')=='analyzing':label+=f" · {max(0,min(99,int(float(live['progress'])*100)))}%"
                    except Exception:pass
                bars=''.join(f'<span style="flex:1;height:4px;border-radius:4px;background:{"#168653" if i<n else "#C3D4DF"}"></span>' for i in range(3))
                cols[3].markdown(f'<div class="v24cell" style="color:{fg}">● {html_lib.escape(label)}<div style="display:flex;gap:3px;align-items:center;margin-top:4px">{bars}<span style="color:#596B80;font-size:11px">{n}/3</span></div></div>',unsafe_allow_html=True)
                for col,val in zip(cols[4:],[html_lib.escape(duration_label(r)),date_cell(created_stamp(r)),date_cell(final_stamp(r))]):col.markdown(f'<div class="v24cell">{val}</div>',unsafe_allow_html=True)
            if not rows:st.caption('검색 결과가 없습니다.')
        st.divider()
        selected=next((r for r in records if r['id']==st.session_state.get('selected_run')),None)
        st.caption('▶ 현재 선택 영상: '+(display_name(selected) if selected else '선택 가능한 완료 영상 없음'))
        st.caption('상태는 선택 모델 기준 · 완료 막대 및 분석 일시는 기존 3개 모델 기준 · — : 미완료 또는 기록 없음')

chosen=st.session_state.get('selected_run') if eligible else None
rec=next((r for r in records if r.get('id')==chosen),None)
seg=str(rec.get('segment','R-001')) if rec else 'R-001'
work='runs/'+chosen+'/'+model_id if chosen else None
ready=False;result={'data_type':'NO_RESULT','detections':[],'summary':{}}
if work and rec and rec.get('models',{}).get(model_id)=='분석 완료':
    try:result=obj(work+'/results.json');ready=True
    except Exception:pass
sim=None
try:
    simulation=get_df(sim,'data/simulation.csv')
    required={'segment_id','month','pothole_count','avg_relative_area','max_relative_area','recurrence_count','traffic_volume','road_age_year','risk_score_before','risk_score_after'}
    if not required.issubset(simulation.columns):st.error('simulation.csv 필수 컬럼 누락: '+str(sorted(required-set(simulation.columns))));st.stop()
    performance=pd.DataFrame([dict(model=v.get('model_name',m),version=v.get('model_revision','미제공'),status=model_label(m),**{k:v.get(k) for k in ['precision','recall','f1','map50','map50_95','fps']}) for m,v in infos.items()]);info=infos.get(model_id,{})
    ranks=ranking(simulation)
    detections=pd.DataFrame(result.get('detections',[]))
except Exception as e:st.error(f'데이터 로딩 오류: {e}');st.stop()

# V15: common fictional road map, no external tiles or credentials.
import plotly.graph_objects as go
road_ids=sorted(ranks.segment_id.astype(str).unique())
if not road_ids: st.error('도로 구간 데이터 없음'); st.stop()
if st.session_state.get('v24_pending_segment') in road_ids:
    st.session_state['road_segment']=st.session_state.pop('v24_pending_segment')
if st.session_state.get('road_segment') not in road_ids:
    st.session_state['road_segment']=seg if seg in road_ids else road_ids[0]

def map_figure(selected, focus):
    import math, random
    fig=go.Figure(); rng=random.Random(46)
    # Fictional city plan: curving river, irregular streets and building footprints.
    def polygon(points, color, outline=None):
        fig.add_trace(go.Scatter(x=[p[0] for p in points]+[points[0][0]],y=[p[1] for p in points]+[points[0][1]],fill='toself',mode='lines',line=dict(color=outline or color,width=0.7),fillcolor=color,hoverinfo='skip',showlegend=False))
    def street(points,width=5,major=False):
        for color,w in [('#c9c6bd',width+2),('#fffdf8' if not major else '#f8e6b6',width)]:
            fig.add_trace(go.Scatter(x=[p[0] for p in points],y=[p[1] for p in points],mode='lines',line=dict(color=color,width=w,shape='spline',smoothing=.65),hoverinfo='skip',showlegend=False))
    polygon([(0,8),(2,9),(4,8.7),(5,10),(0,10)],'#c8dfbb')
    polygon([(10,0),(14,0),(14,3),(12,2.5),(10,1.4)],'#c8dfbb')
    polygon([(5,4),(6.8,4.3),(7.4,5.6),(6.2,6.2),(4.9,5.4)],'#c9dfba')
    river=[(0,2.1),(2,2.5),(4,1.8),(6,1.2),(8,1.7),(10,3.0),(12,3.4),(14,2.9)]
    polygon([(x,y+.42) for x,y in river]+[(x,y-.42) for x,y in reversed(river)],'#a5d4e8')
    # Six irregular corridors, each divided into five contiguous management segments.
    corridors=[[(.5,8.2),(2.5,7.7),(4.8,8.2),(7.2,7.5),(10,8.4),(13.5,8.0)],[(.4,6.5),(2.6,6.8),(4.7,6.3),(7.4,6.8),(10.3,6.1),(13.6,6.6)],[(.5,4.3),(2.8,4.8),(4.7,4.0),(7.6,4.5),(10.1,4.8),(13.5,4.2)],[(.5,.8),(2.9,1.0),(5.1,.5),(7.8,.6),(10.4,1.2),(13.5,1.0)],[(2.5,9.7),(2.5,7.7),(2.6,6.8),(2.8,4.8),(2.5,2.4),(2.9,1.0)],[(10.7,9.7),(10,8.4),(10.3,6.1),(10.1,4.8),(10.4,3.1),(10.4,1.2)]]
    # Building clusters follow neighborhood blocks, avoiding river and primary corridors.
    def dist(x,y,a,b):
        dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy or 1)));return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
    edges=[(a,b) for path in corridors+[river] for a,b in zip(path,path[1:])]
    for _ in range(280):
        x=rng.uniform(.3,13.7);y=rng.uniform(.3,9.7)
        if min(dist(x,y,a,b) for a,b in edges)<.46 or (5<x<7.4 and 4<y<6.2) or (x<4 and y>8.7):continue
        w=rng.uniform(.10,.32);h=rng.uniform(.09,.25); angle=rng.uniform(-.25,.25)
        pts=[(x+u*math.cos(angle)-v*math.sin(angle),y+u*math.sin(angle)+v*math.cos(angle)) for u,v in [(-w,-h),(w,-h),(w,h),(-w,h)]]
        polygon(pts,rng.choice(['#ded9d0','#e5dfd5','#d6d3cc']),'#f7f5ef')
    for x in [1.2,4.2,6.8,8.7,12.2]:
        street([(x,9.7),(x+.3,8.1),(x-.2,6.6),(x+.35,4.4),(x+.1,3.7)],3)
    for y in [5.5,7.4,9.1]:street([(.2,y),(3,y+.2),(6,y-.25),(9,y+.15),(13.8,y-.1)],3)
    for path in corridors:street(path,11,True)
    colors={'관찰':'#269447','주의':'#d7a000','우선 점검':'#e87924','즉시 점검 권고':'#c62838'}
    segments=[(a,b) for path in corridors for a,b in zip(path,path[1:])];centers={}
    for k,sid in enumerate(road_ids):
        a,b=segments[k%len(segments)]; x=(a[0]+b[0])/2;y=(a[1]+b[1])/2;centers[sid]=(x,y)
        r=ranks.loc[ranks.segment_id.astype(str)==sid].iloc[0];c=colors.get(r.grade,'#64748b');active=sid==selected
        if active:fig.add_trace(go.Scatter(x=[a[0],b[0]],y=[a[1],b[1]],mode='lines',line=dict(color='#173b55',width=15),hoverinfo='skip',showlegend=False))
        fig.add_trace(go.Scatter(x=[a[0],x,b[0]],y=[a[1],y,b[1]],mode='lines+markers+text',line=dict(color=c,width=9 if active else 5),marker=dict(size=[0,13 if active else 7,0],color=c,line=dict(color='white',width=1)),text=['',sid,''],textposition='top center',textfont=dict(size=12 if active else 9,color='#173b55'),customdata=[sid]*3,hovertemplate=sid+' · '+str(r.grade)+' · '+f'{r.risk_score:.1f}/100<extra></extra>',showlegend=False))
    for x,y,label in [(2,9.4,'북부공원'),(6.1,5.5,'중앙공원'),(8.4,2.5,'가람천'),(12.4,7.3,'상업지구'),(4.1,3.4,'주거지구')]:
        fig.add_annotation(x=x,y=y,text=label,showarrow=False,font=dict(size=10,color='#64766b'))
    x,y=centers[selected]
    fig.update_layout(height=510,margin=dict(l=4,r=4,t=8,b=4),paper_bgcolor='#f5f8fa',plot_bgcolor='#f1eee5',dragmode='pan',clickmode='event+select',xaxis=dict(visible=False,range=[x-3.2,x+3.2] if focus else [0,14]),yaxis=dict(visible=False,range=[y-2.8,y+2.8] if focus else [0,10],scaleanchor='x',scaleratio=1),showlegend=False)
    return fig

def map_pick():
    event=st.session_state.get('road_map_chart',{})
    points=event.get('selection',{}).get('points',[])
    if points:
        sid=points[-1].get('customdata')
        if isinstance(sid,str) and sid in road_ids: st.session_state['road_segment']=sid

control,map_button=st.columns([3,1])
with control:
    seg=st.selectbox('도로 구간 (전체 화면 공통)',road_ids,key='road_segment')
with map_button:
    if 'road_map_open' not in st.session_state: st.session_state['road_map_open']=False
    def toggle_road_map():
        st.session_state['road_map_open']=not st.session_state['road_map_open']
    st.button('🗺 지도 닫기' if st.session_state['road_map_open'] else '🗺 도로 구간 지도',key='road_map_toggle',on_click=toggle_road_map,use_container_width=True)
if st.session_state['road_map_open']:
    st.markdown("""<style>[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .road-map-anchor){position:fixed;right:2rem;top:9rem;width:min(650px,90vw);max-height:75vh;overflow:auto;z-index:900;background:#f5f8fa;border:1px solid #b5cbd7;border-radius:14px;padding:16px;box-shadow:0 8px 32px #173b5533;} @media(max-width:700px){[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .road-map-anchor){right:2vw;top:8rem;width:96vw;max-height:70vh;}}</style>""",unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<span class="road-map-anchor"></span>',unsafe_allow_html=True)
        map_title,map_close=st.columns([7,1],vertical_alignment='center')
        with map_title:
            st.markdown('<h3 class="road-map-drag" style="cursor:grab;touch-action:none;user-select:none;margin:0">⠿ 도로 구간 위치 · 가상 지도</h3>',unsafe_allow_html=True)
        with map_close:
            def close_road_map():
                st.session_state['road_map_open']=False
            st.button('✕',key='road_map_close_x',help='지도 닫기',on_click=close_road_map,use_container_width=True)
        import streamlit.components.v1 as map_components
        map_components.html("""<script>
(()=>{try{
 const w=window.parent,d=w.document,K='roadcare-map-position-v19';
 const sel='[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .road-map-anchor)';
 if(w.__roadMapDragCleanup)w.__roadMapDragCleanup();
 let active=null;
 function clamp(p,x,y){return [Math.max(0,Math.min(x,w.innerWidth-p.offsetWidth)),Math.max(0,Math.min(y,w.innerHeight-Math.min(p.offsetHeight,90)))];}
 function place(p,x,y){[x,y]=clamp(p,x,y);p.style.setProperty('left',x+'px','important');p.style.setProperty('top',y+'px','important');p.style.setProperty('right','auto','important');return [x,y];}
 function restore(){const p=d.querySelector(sel);if(!p||active)return;try{const v=JSON.parse(w.sessionStorage.getItem(K));if(Array.isArray(v)&&v.length===2)place(p,...v);}catch(e){}}
 function down(e){const h=e.target.closest('.road-map-drag');if(!h||e.button!==0)return;const p=h.closest(sel);if(!p)return;const r=p.getBoundingClientRect();active={p,dx:e.clientX-r.left,dy:e.clientY-r.top,id:e.pointerId,h};h.style.cursor='grabbing';try{h.setPointerCapture(e.pointerId);}catch(_){}e.preventDefault();}
 function move(e){if(!active||active.id!==e.pointerId)return;const v=place(active.p,e.clientX-active.dx,e.clientY-active.dy);try{w.sessionStorage.setItem(K,JSON.stringify(v));}catch(_){}e.preventDefault();}
 function up(e){if(!active||active.id!==e.pointerId)return;active.h.style.cursor='grab';active=null;}
 d.addEventListener('pointerdown',down);d.addEventListener('pointermove',move,{passive:false});d.addEventListener('pointerup',up);d.addEventListener('pointercancel',up);w.addEventListener('resize',restore);
 const obs=new w.MutationObserver(restore);obs.observe(d.body,{childList:true,subtree:true});restore();
 w.__roadMapDragCleanup=()=>{obs.disconnect();d.removeEventListener('pointerdown',down);d.removeEventListener('pointermove',move);d.removeEventListener('pointerup',up);d.removeEventListener('pointercancel',up);w.removeEventListener('resize',restore);};
 }catch(e){console.warn('RoadCare map drag unavailable',e);}})();
</script>""",height=0,scrolling=False)
        st.caption('실제 지리 좌표가 아닌 기능 테스트용 지도 · '+str(len(road_ids))+'개 구간')
        focus=st.toggle('선택 구간 자동 확대',value=False,key='road_map_focus')
        st.plotly_chart(map_figure(seg,focus),key='road_map_chart',on_select=map_pick,selection_mode='points',use_container_width=True,config={'scrollZoom':True,'displaylogo':False})
        st.caption('제목을 드래그하면 창 이동 · 지도 내부 드래그는 지도 이동 · 휠 확대/축소 · 도로 중앙 점 클릭으로 구간 선택 · 상단 지도 버튼 또는 ✕ 버튼으로 닫기')
        st.caption('🟢 관찰 (30 미만) · 🟡 주의 (30–60 미만) · 🟠 우선 점검 (60–80 미만) · 🔴 즉시 점검 권고 (80 이상)')
        selected_row=ranks.loc[ranks.segment_id.astype(str)==seg].iloc[0]
        st.write(f'**{seg}** · {selected_row.grade} · Risk {selected_row.risk_score:.1f}/100 · 순위 {int(selected_row["rank"])} / {len(road_ids)}')
row=ranks.loc[ranks.segment_id.astype(str)==seg].iloc[0]
# Video summary must retain the actual registered video's segment, not map browsing selection.
video_seg=str(rec.get('segment','')) if rec else ''
video_rows=ranks.loc[ranks.segment_id.astype(str)==video_seg]
video_risk=f'{video_rows.iloc[0].risk_score:.1f}' if not video_rows.empty else '—'

if page=='영상 분석':
    main,side=st.columns([2.15,1],gap='small')
    with main:
        st.markdown('### 원본 영상 / AI 분석 영상')
    if rec:
        with main:st.caption(display_name(rec)+' · '+status_label(rec)+' · 등록 구간 '+video_seg)
    left=right=None
    if chosen:
        try:left=read('runs/'+chosen+'/original.mp4')
        except Exception:st.caption('원본 영상 수신 대기')
        if ready:
            try:right=read(work+'/result.mp4')
            except Exception:st.caption('분석 영상 수신 대기')
    with main:
        with st.container(border=True):player_html(left,right,mode,detections,ready,playback_key=str(chosen)+'/'+str(model_id))
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
        st.caption(status+' · '+infos[model_id].get('model_name',model_id))
        if data is None:
            st.info('선택한 영상과 모델의 분석 데이터가 아직 없습니다.');return
        if data.get('progress') is not None: st.progress(max(0.,min(1.,float(data['progress']))),text='분석 진행률')
        elif ready: st.progress(1.,text='분석 진행률 · 100%')
        st.caption('수신 확인: '+datetime.now(timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('Asia/Seoul')).strftime('%H:%M:%S')+' · 2초 주기 조회 (전송 지연 가능)')
        st.caption('실제 모델 데이터 · '+str(data.get('data_type','')))
        d=pd.DataFrame(data.get('detections',[])); summary=data.get('summary',{})
        conf=pd.to_numeric(d.get('confidence',pd.Series(dtype=float)),errors='coerce'); area=pd.to_numeric(d.get('relative_area',pd.Series(dtype=float)),errors='coerce')
        def fmt(x):return f'{x:.4f}' if pd.notna(x) else '—'
        if part=='summary':
            for col,(label,value) in zip(st.columns(2),[('누적 탐지 이벤트',summary.get('cumulative_detection_events','—')),('고유 Track',summary.get('current_cycle_unique_count','—'))]):col.metric(label,value)
            for col,(label,value) in zip(st.columns(2),[('평균 Confidence',fmt(conf.mean())),('최대 Confidence',fmt(conf.max()))]):col.metric(label,value)
            for col,(label,value) in zip(st.columns(3),[('평균 Relative Area',fmt(area.mean())),('최대 Relative Area',fmt(area.max())),('Risk Score · 영상 등록 구간',video_risk)]):col.metric(label,value)
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
    with st.container(border=True):live_panel("charts")
    list_panel()
    if rec:
        with st.container(border=True):
            st.markdown('### 영상 정보')
            if rec:
                st.write(display_name(rec))
                st.write('영상 길이: '+duration_label(rec));st.write('업로드 일시: '+fmt_stamp(created_stamp(rec)))
                st.write('분석 일시: '+fmt_stamp(final_stamp(rec)))
            else:st.caption('선택된 영상 없음')
    if ready:
        st.write('실측 추론 FPS:',result.get('summary',{}).get('inference_fps','—'))
        st.download_button('결과 JSON',json.dumps(result,ensure_ascii=False).encode(),'results.json')
        for label,name in [('탐지 CSV','detections.csv'),('분석 영상','result.mp4')]:
            try:st.download_button(label,read(work+'/'+name),name)
            except Exception:st.caption(label+' 미수신')
if page=='도로 위험도·우선순위':
    st.subheader(f'{len(road_ids)}개 도로구간 위험도 및 유지관리 우선순위')
    st.warning('연습용 가상 데이터 · 실제 탐지 결과와 합산하지 않음')
    a,b,c,d=st.columns(4)
    for col,label,val in [(a,'Risk Score',f'{row.risk_score:.1f}/100'),(b,'위험등급',row.grade),(c,'현재 순위',f'{int(row["rank"])}/{len(road_ids)}'),(d,'포트홀 수 (시뮬레이션)',int(row.pothole_count))]:col.metric(label,val)
    advice={'관찰':'정기 모니터링','주의':'현장 상태 점검','우선 점검':'단기간 내 현장점검과 보수 검토','즉시 점검 권고':'우선 현장확인과 신속한 보수 검토'}
    st.info(f'{seg} 유지관리 권고: {advice[row.grade]}')
    a,b=st.columns([2,1])
    with a:st.dataframe(ranks[['rank','segment_id','risk_score','grade','pothole_count','recurrence_count','traffic_volume','road_age_year']],use_container_width=True,hide_index=True)
    with b:plot(px.bar(ranks.head(5).sort_values('risk_score'),x='risk_score',y='segment_id',orientation='h',title='위험도 Top 5'))
    download('전체 구간 순위 CSV',ranks,'segment_ranking.csv')
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
    st.write('현재 모델 버전:',info.get('model_revision','미제공'))
    st.write('선정 근거:',info.get('selection_reason','미제공'))
    download('모델 비교 CSV',performance,'model_performance.csv')
with st.expander('데이터 다운로드'):
    st.divider();st.subheader('데이터 다운로드')
    st.download_button('results.json',json.dumps(result,ensure_ascii=False,indent=2).encode(),file_name='results.json')
    download('simulation.csv',simulation,'simulation.csv')
    download('model_performance.csv',performance,'model_performance.csv')
