GitHub main / RoadCare_AI_Web_Dashboard_V3 폴더에 이 폴더의 내용 업로드. 기존 파일 백업 권장.
Streamlit Cloud main file path: RoadCare_AI_Web_Dashboard_V3/app.py
Secrets: 기존 [supabase] url, secret_key, bucket 설정 유지. 실제 키는 GitHub에 올리지 말 것.
앱 접근은 비공개/허용 사용자로 제한 (서버가 Storage 비밀 키 사용).
로컬 V6 Triple의 sync/catalog_v6.json 및 runs/{id}/{model}/ 구조를 읽음.
실제 모델 가중치 불필요. simulation.csv는 가상 데이터. GPS 좌표 미제공으로 구간 격자 사용.
로컬 실행: python -m pip install -r requirements.txt ; python -m streamlit run app.py
