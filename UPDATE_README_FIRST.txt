BizLab v0.7 전체 수정본 (2026-11-08)

[오류 원인]
배포된 app.py에서 simulate(... other_variable_share_pct=..., reference_sales_manwon=...) 호출.
실행 중인 model_v05.py의 simulate() 정의가 구버전이면 TypeError가 발생합니다.

[올바른 교체 방법]
1. GitHub Desktop > Fetch origin 을 눌러 최신 저장소를 받고, 필요하면 Pull origin.
2. Show in Explorer로 GitHub 로컬 저장소 최상위 폴더를 엽니다.
3. 이 ZIP을 풀어 나온 파일/폴더 내용물을 전부 복사해 저장소 최상위에 붙여넣습니다.
   기존 파일은 '덮어쓰기'를 선택하세요. ZIP이나 v0.7 상위폴더를 그대로 넣지 마세요.
4. GitHub Desktop Changes에서 app.py와 model_v05.py가 변경되었는지 확인합니다.
5. Commit to main -> Push origin 순서대로 클릭하세요. Commit만으로는 배포되지 않습니다.
6. 웹에서 Ctrl+Shift+R 새로고침합니다.

[배포 전 로컬 검증]
저장소 폴더에서: py -m unittest discover -v
실행: py -m streamlit run app.py

주의: 이미 수정된 파일과 같은 내용이라면 Changes에 안 나타날 수 있습니다.
그 경우 GitHub 웹의 model_v05.py에서 def simulate를 찾아
other_variable_share_pct, reference_sales_manwon 인자가 있는지 확인하세요.
