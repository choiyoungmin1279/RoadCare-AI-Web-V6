"""Private Supabase Storage link. Keep secret keys in Streamlit secrets only."""
import json
from urllib.parse import quote

import requests
import streamlit as st

TIMEOUT = 90


def settings():
    try:
        c = st.secrets["supabase"]
        url = str(c["url"]).strip().rstrip("/")
        key = str(c["secret_key"]).strip()
        bucket = str(c.get("bucket", "roadcare-videos")).strip()
        if not url.startswith("https://") or not key or "PASTE_" in key or not bucket:
            return None
        return url, key, bucket
    except (KeyError, FileNotFoundError, AttributeError):
        return None


def _headers(key, content_type=None, upsert=False):
    # New Supabase sb_secret_* keys are not JWTs. Sending them as Bearer
    # tokens causes Storage to respond with "Invalid Compact JWS".
    headers = {"apikey": key}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    if content_type:
        headers["Content-Type"] = content_type
    if upsert:
        headers["x-upsert"] = "true"
    return headers


def _request(method, path, data=None, content_type=None, upsert=False):
    cfg = settings()
    if not cfg:
        raise RuntimeError("Supabase 설정이 없습니다. .streamlit/secrets.toml 또는 Streamlit Cloud Secrets를 확인하세요.")
    url, key, _ = cfg
    response = requests.request(
        method,
        url + "/storage/v1/object/" + path,
        headers=_headers(key, content_type, upsert),
        data=data,
        timeout=TIMEOUT,
    )
    if not response.ok:
        raise RuntimeError(f"Supabase HTTP {response.status_code}: {response.text[:250]}")
    return response


def put(name, content, mime):
    cfg = settings()
    if not cfg:
        raise RuntimeError("Supabase 연결 설정 없음")
    path = quote(cfg[2] + "/" + name, safe="/")
    return _request("POST", path, data=content, content_type=mime, upsert=True)


def get(name):
    cfg = settings()
    if not cfg:
        raise RuntimeError("Supabase 연결 설정 없음")
    path = quote(cfg[2] + "/" + name, safe="/")
    return _request("GET", "authenticated/" + path).content


def put_manifest(obj):
    put("sync/latest.json", json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json")


def get_manifest():
    try:
        return json.loads(get("sync/latest.json"))
    except RuntimeError as exc:
        if "HTTP 404" in str(exc) or "HTTP 400" in str(exc):
            return None
        raise

def delete_objects(names):
    cfg=settings()
    if not cfg: raise RuntimeError('Supabase 설정 없음')
    return _request('DELETE',quote(cfg[2],safe=''),data=json.dumps({'prefixes':names}),content_type='application/json')
