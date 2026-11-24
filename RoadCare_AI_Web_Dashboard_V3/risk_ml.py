import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor

WEIGHTS={'pothole_count':.30,'avg_relative_area':.25,'recurrence_count':.20,'traffic_volume':.15,'road_age_year':.10}
LIMITS={'pothole_count':(0,25),'avg_relative_area':(0,.15),'recurrence_count':(0,15),'traffic_volume':(0,40000),'road_age_year':(0,40)}
def risk(row):
    return round(float(np.clip(sum(np.clip((float(row.get(k,0))-LIMITS[k][0])/(LIMITS[k][1]-LIMITS[k][0]),0,1)*w for k,w in WEIGHTS.items())*100,0,100)),2)
def grade(v):
    return '관찰' if v<30 else '주의' if v<60 else '우선 점검' if v<80 else '즉시 점검 권고'
def ranking(df,month=None,overrides=None):
    x=df.copy(); x['month']=x['month'].astype(str)
    if month is None:month=x['month'].max()
    x=x[x.month==month].copy()
    if overrides:
        for sid,vals in overrides.items():
            for k,v in vals.items():
                if k in x.columns:x.loc[x.segment_id==sid,k]=v
    x['risk_score']=x.apply(risk,axis=1);x['grade']=x.risk_score.map(grade)
    return x.sort_values(['risk_score','segment_id'],ascending=[False,True]).assign(rank=lambda z:range(1,len(z)+1))
def insights(df):
    cols=['pothole_count','avg_relative_area','max_relative_area','recurrence_count','traffic_volume','road_age_year']
    latest=df.sort_values('month').groupby('segment_id').tail(1).copy()
    x=latest[cols].apply(pd.to_numeric,errors='coerce').fillna(0)
    model=IsolationForest(random_state=20261126,contamination=.15)
    latest['anomaly_score']=model.fit(x).decision_function(x);latest['anomaly']=model.predict(x)==-1
    return latest.sort_values('anomaly_score')
def forecast(df):
    data=df.sort_values(['segment_id','month']).copy()
    data['lag1']=data.groupby('segment_id').pothole_count.shift(1)
    data['lag2']=data.groupby('segment_id').pothole_count.shift(2)
    data['month_num']=pd.to_datetime(data.month+'-01').dt.month
    feats=['lag1','lag2','avg_relative_area','recurrence_count','traffic_volume','road_age_year','month_num']
    train=data.dropna(subset=['lag1','lag2']).copy()
    if len(train)<20:return pd.DataFrame(),None
    months=sorted(train.month.unique());split=months[-3] if len(months)>3 else months[-1]
    a=train[train.month<split];b=train[train.month>=split]
    if a.empty:return pd.DataFrame(),None
    m=RandomForestRegressor(n_estimators=80,max_depth=8,random_state=20261126,n_jobs=1)
    m.fit(a[feats].fillna(0),a.pothole_count)
    mae=float(np.abs(m.predict(b[feats].fillna(0))-b.pothole_count).mean()) if not b.empty else None
    m.fit(train[feats].fillna(0),train.pothole_count)
    last=data.groupby('segment_id').tail(1).copy();last['lag2']=last['lag1'];last['lag1']=last['pothole_count'];last['month_num']=(last.month_num%12)+1
    last['next_month_prediction']=np.maximum(0,m.predict(last[feats].fillna(0))).round(2)
    return last[['segment_id','next_month_prediction']],mae
