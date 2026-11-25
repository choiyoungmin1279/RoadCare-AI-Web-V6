RoadCare AI Web V10 / Local V8 CPU 호환용
1. 기존 GitHub 저장소를 백업합니다.
2. ZIP 내부 RoadCare_AI_Web_Dashboard_V3 폴더의 파일을 기존 동일 경로에 덮어씁니다. 루트 .streamlit/config.toml도 적용합니다.
3. Streamlit Cloud entrypoint: RoadCare_AI_Web_Dashboard_V3/app.py (기존 주소 유지).
4. 기존 Cloud Secrets [supabase] url, secret_key, bucket 유지. 비밀키는 GitHub에 올리지 마세요.
5. 로컬 V8에서 영상 등록 및 분석 시작, 웹에서 영상과 모델 선택. 목록과 live.json을 2초마다 조회합니다. 분석 영상은 완료 전송 후 재생됩니다.
6. 영상 표시 이름은 web_metadata/{run_id}.json에 저장되며 로컬 파일명과 별개입니다. 웹 방문자가 이름을 변경할 수 있으므로 신뢰할 수 있는 사용자에게만 접근을 허용하세요. 기존 로컬 삭제 시 목록에서 사라지지만 별도 이름 메타데이터는 저장소에 남을 수 있습니다.
7. 영상 정보 버튼에서 정보 조회를 누르면 원본 영상 길이와 Storage 객체 생성 날짜를 확인합니다. 과거 객체 생성 날짜가 없으면 확인 불가로 표시합니다.
8. 자동/PC/모바일 화면 모드. 브라우저 자동재생 제한 시 동시 재생 버튼을 누르세요.
9. 실제 탐지와 가상 위험도 데이터 분리. 시간별 그래프는 신규 Track 기준입니다.
10. Python 문법 및 ZIP 검사만 수행. 실제 Streamlit, Supabase, 모바일 테스트는 배포 후 필요합니다. 대용량 영상은 기존 base64 방식의 메모리 및 전송 부담이 있습니다.
