# 진행 상황

> 이 파일 하나로 전체 맥락 파악 가능. 세션 시작 시 이 파일만 읽고 이어서 진행할 것.

## 아키텍처 결정
- 구조: `engine/`(FastAPI, 로직) ↔ `ui/`(React+TS, 화면 전용, API만 호출). Tauri 패키징은 보류(CLAUDE.md 방침).
- `engine/app/api/*`: FastAPI 라우터(얇은 계층, HTTP만 담당) / `engine/app/core/<feature>/*`: 프레임워크 비의존 순수 로직(단위테스트 대상) / `engine/app/models/*`: pydantic 스키마 / `engine/app/storage/*`: SQLite(db.py)+YAML(yaml_store.py).
- SQLite = 로컬 조회/캐시 인덱스(재생성 가능, git 비대상, `.gitignore`). YAML = Git diff 대상 선언형 모델 원본(추후 유닛에서 도입).
- Python: venv+pip (`engine/.venv`, `engine/requirements.txt`). Node: npm+Vite(예정).
- sqlite3 connection은 `check_same_thread=False`로 오픈(FastAPI가 sync 의존성/async 핸들러를 다른 스레드에서 실행할 수 있어서 필요; 1인 로컬 툴이라 동시쓰기 경합 없음).
- F-101 표준사전 시드: 사용자가 제공한 실제 행정안전부 공공데이터 공통표준용어 CSV(2026-07-31, 13,176행) → `engine/app/data/dictionary/standard_terms.csv`에 번들.
- F-103 방향(검토보고서 권고 반영): "완전 자동 합성"이 아니라 사전 최대일치(forward maximum matching) 기반 "자동 추천 + 사용자 확정" 구조로 간다. 표준 CSV에는 개별 단어(고객/주문 등) 단위 사전이 없고 복합 "용어" 단위만 있어, 미등록 구간은 세그먼트로 남겨 사용자가 채우게 함.
- 커스텀 사전(F-106) 조회 우선순위가 표준 사전보다 항상 높음(override).

## 완료
- [x] Unit 0: 저장 기반 — `engine/app/storage/db.py`, `yaml_store.py`. 테스트 `tests/test_storage.py` (4).
- [x] Unit 1: F-101/F-106 사전
  - `core/dictionary/domain_code.py`: 도메인코드(`명V100` 등) 파서 → data_type/length/precision/scale
  - `core/dictionary/importer.py`: 표준CSV 파서(고정 컬럼) + 커스텀CSV 파서(헤더 별칭 매핑, term/abbreviation 필수)
  - `core/dictionary/repository.py`: SQLite upsert(source별 전체 재적재)/조회(정확일치+동의어, custom 우선)/목록·카운트
  - `core/dictionary/matcher.py`: 전방 최대일치 세그먼터 (F-103 기반)
  - `api/dictionary.py`: POST /dictionary/import/standard, POST /dictionary/import/custom, GET /dictionary/terms, GET /dictionary/lookup, GET /dictionary/segment
  - 테스트 35개 (domain_code, importer, repository, matcher, api) + 실서버 curl 스모크 확인(13,168건 임포트/조회/세그먼트 정상)
  - 전체 테스트: `cd engine && source .venv/bin/activate && python -m pytest -q` → 39 passed

## 다음 (우선순위 순, 기능정의서 6장 기준)
- [ ] Unit 2: F-102 엑셀/노션 스크랩북 파싱 (그리드 Copy&Paste 파싱) + UI 스캐폴드 최초 연결(Vite+React+TS)
- [ ] Unit 3: F-103 물리명 합성 UI/린터 (Unit1 matcher를 실제 화면과 연결, 실시간 경고)
- [ ] Unit 4: F-104a 대리키 전환 + JPA 코드 추출
- [ ] Unit 5: F-105 레거시 DDL 역엔지니어링 + 폴백 UI
- [ ] Unit 6: F-201 암호화 대상 감지 + 길이 계산
- [ ] Unit 7: F-203a DBMS 락 방지 가이드
- [ ] Unit 8: F-301 Excel/PDF 산출물 출력

## 실행 방법
```bash
cd engine && source .venv/bin/activate
python -m pytest -q                          # 테스트
uvicorn app.main:app --reload --port 8000    # 서버 (UI 개발서버는 5173 가정, CORS 허용됨)
```

## 확인이 필요했던 결정 (히스토리)
- 2026-07-31: F-101 시드 데이터 출처 → 사용자가 실제 행안부 CSV 직접 제공(위 참고).
