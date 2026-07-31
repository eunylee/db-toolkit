# 진행 상황

> 이 파일 하나로 전체 맥락 파악 가능. 세션 시작 시 이 파일만 읽고 이어서 진행할 것.

## 아키텍처 결정
- 구조: `engine/`(FastAPI, 로직) ↔ `ui/`(React+TS, 화면 전용, API만 호출). Tauri 패키징은 보류(CLAUDE.md 방침).
- `engine/app/api/*`: FastAPI 라우터(얇은 계층, HTTP만 담당) / `engine/app/core/<feature>/*`: 프레임워크 비의존 순수 로직(단위테스트 대상) / `engine/app/models/*`: pydantic 스키마 / `engine/app/storage/*`: SQLite(db.py)+YAML(yaml_store.py).
- SQLite = 로컬 조회/캐시 인덱스(재생성 가능, git 비대상, `.gitignore`). YAML = Git diff 대상 선언형 모델 원본(추후 유닛에서 도입).
- Python: venv+pip (`engine/.venv`, `engine/requirements.txt`). Node: npm+Vite (`ui/`, react-ts 템플릿, vitest+RTL).
- `ui/src` 구조: `shared/api/client.ts`(공용 fetch 래퍼, 화면은 이걸로만 엔진 호출) / `features/<feature>/{model,ui,api}`(model=순수 로직·단위테스트, ui=React 컴포넌트, api=엔진 호출). 새 기능도 이 3분할 패턴 반복.
- F-102 스크랩북: 클립보드 paste 캡처(브라우저에서만 가능)만 화면이 하고, 실제 TSV 파싱은 `POST /scrapbook/parse`(엔진)에서 수행 → 엔진/화면 분리 원칙 준수. 파싱은 stdlib `csv`를 tab 구분자로 재사용(따옴표로 감싼 셀 안의 탭/개행도 처리됨).
- sqlite3 connection은 `check_same_thread=False`로 오픈(FastAPI가 sync 의존성/async 핸들러를 다른 스레드에서 실행할 수 있어서 필요; 1인 로컬 툴이라 동시쓰기 경합 없음).
- F-101 표준사전 시드: 사용자가 제공한 실제 행정안전부 공공데이터 공통표준용어 CSV(2026-07-31, 13,176행) → `engine/app/data/dictionary/standard_terms.csv`에 번들.
- F-103 방향(검토보고서 권고 반영): "완전 자동 합성"이 아니라 사전 최대일치(forward maximum matching) 기반 "자동 추천 + 사용자 확정" 구조로 간다. 표준 CSV에는 개별 단어(고객/주문 등) 단위 사전이 없고 복합 "용어" 단위만 있어, 미등록 구간은 세그먼트로 남겨 사용자가 채우게 함.
- 커스텀 사전(F-106) 조회 우선순위가 표준 사전보다 항상 높음(override).
- **F-102는 완전 자유 그리드로 유지한다** (헤더 강제 없음). 논리명/물리명/데이터타입/PK 컬럼은 F-102(원본 캡처)의 입력값이 아니라 F-103/F-104a에서 만들어지는 결과값이라, 별도의 "테이블 설계" 화면(`features/table-designer`)에서 다룬다.
- **PK**: 단일 테이블 안의 속성일 뿐이라 체크박스로 충분 (F-104a가 사용).
- **FK/관계선은 필수 9개 기능에 원래 없다.** 기능정의서에 "ERD 그리기" 항목 자체가 없고, 다중 테이블 FK 연쇄(F-104b)는 명시적으로 "선택" 제외 대상. 다만 (a) CLAUDE.md 원칙("ERD 표기법 Barker/IE 토글")과 (b) F-105(필수)의 PRD 테스트케이스(TC-105-01, "ERD 다이어그램을 그리는데 성공")가 ERD *시각화*는 요구해서, 아래 Unit 4/5로 필요 인프라를 추가함:
  - 그린필드(신규 설계): 관계선은 자동 추측하지 않음(컬럼명만으로 참조 테이블을 확신할 수 없음) → 사용자가 **드래그로 수동 연결**(Unit 5)
  - 레거시(F-105, Unit 7): 기존 DDL의 FK 제약조건을 파싱해 **자동으로 관계선 렌더** (유일하게 자동화 가능한 케이스, 이미 명시된 제약조건을 읽는 것뿐이라 추측이 아님)
  - `erd_notation_prototype.jsx`(Barker/IE 토글 렌더러)를 실제 데이터 기반으로 전환해 재사용
- Unit 3에서 API 라우터 중복 의존성 버그 발견/수정: 라우터마다 개별 `_db()` 의존성을 정의하면 테스트의 `dependency_overrides`가 다른 라우터엔 적용 안 됨 → `app/api/deps.py`의 공유 `get_db`로 통일.
- pydantic `model_dump()`는 Enum을 그대로 두므로 YAML(safe_load) 왕복이 깨짐 → YAML/JSON 직렬화 전에는 항상 `model_dump(mode="json")` 사용.

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
- [x] Unit 2: F-102 엑셀/노션 스크랩북 + UI 스캐폴드 최초 연결
  - `core/scrapbook/parser.py`: TSV 그리드 파서 (ragged 행 padding, 꼬리 빈행 제거, 따옴표 셀 처리) / `api/scrapbook.py`: POST /scrapbook/parse
  - 백엔드 테스트 11개 추가 (엣지케이스 포함) → 전체 50 passed
  - `ui/`: Vite+React+TS 스캐폴드, `features/scrapbook/{model/gridMerge.ts, api/scrapbookApi.ts, ui/ScrapbookGrid.tsx}` — 임의 셀(anchor)에 붙여넣으면 엔진 API로 파싱 후 그리드에 병합(필요시 행/열 자동 확장)
  - 프런트 테스트 14개 (vitest+RTL) 통과, `tsc -b` 통과
  - 실브라우저(Chrome) E2E 확인: 클립보드 paste 이벤트 → 엔진 파싱 → 포커스된 셀 기준 정확히 병합됨, 콘솔 에러 없음
  - 실행: 엔진(`uvicorn app.main:app --reload --port 8000`) + `cd ui && npm run dev` (기본 5173, CORS 허용됨)
  - 프런트 테스트: `cd ui && npm run test` / 타입체크: `npx tsc -b`
- [x] Unit 3: 테이블 모델 + F-103 물리명 합성 연결
  - `app/models/naming.py`(NameSuggestion/ColumnSuggestion), `core/naming/suggest.py`(suggest_name/suggest_column — 완전매칭일 때만 물리명 제안, 데이터타입은 마지막 매칭 세그먼트 기준으로 부분매칭이어도 채움)
  - `app/models/tables.py`(Column/Table), `core/tables/repository.py`(YAML 저장, logical_name 기준 upsert) — 워크스페이스 경로는 `engine/app/data/workspace/model.yaml` (개발용 기본값, git 비대상; 실사용 시 클라이언트 프로젝트 자체 git으로 대체될 자리)
  - `api/naming.py`: POST /naming/suggest (배치) / `api/tables.py`: GET·POST /tables, GET /tables/{name}
  - 백엔드 테스트 18개 추가 → 전체 68 passed
  - `ui/features/table-designer/`: model(columnDraft.ts, 순수 병합/변환 로직)/api/ui(TableDesigner.tsx) — 논리명 입력 → "물리명 제안 적용" → 완전매칭은 물리명·타입 채움, 부분매칭은 사용자가 적은 물리명 보존하고 "미등록: X" 경고만 표시 → PK 체크 → "테이블로 저장"
  - 프런트 테스트 10개 추가 → 전체 24 passed, 타입체크 통과
  - 실브라우저 E2E 확인: 완전매칭(고객등록번호→CUST_REG_NO, PK 체크, 저장 후 GET /tables/고객으로 영속 확인) + 부분매칭(VIP고객 → "미등록: VIP" 표시, 물리명 안 지어냄) 둘 다 정상

## 다음 (Unit 3 이후 재정렬됨 — 아래 "PK/FK/ERD 스코프" 참고)
- [ ] Unit 4: ERD 시각화 (읽기전용, 관계선 없음) — `erd_notation_prototype.jsx`를 실제 테이블 데이터 기반으로 전환
- [ ] Unit 5: 관계선 드래그 연결 (수동) — 컬럼 앵커 드래그 → 카디널리티 지정 → 저장/재렌더
- [ ] Unit 6: F-104a 대리키 전환 + JPA 코드 추출
- [ ] Unit 7: F-105 레거시 DDL 역엔지니어링 + 폴백 UI (FK 자동 파싱 → 관계선 자동 렌더)
- [ ] Unit 8: F-201 암호화 대상 감지 + 길이 계산
- [ ] Unit 9: F-203a DBMS 락 방지 가이드
- [ ] Unit 10: F-301 Excel/PDF 산출물 출력

## 실행 방법
```bash
cd engine && source .venv/bin/activate
python -m pytest -q                          # 백엔드 테스트
uvicorn app.main:app --reload --port 8000    # 백엔드 서버

cd ui && npm run dev                          # 프런트 서버 (http://localhost:5173, CORS 허용됨)
npm run test                                  # 프런트 테스트 (vitest)
npx tsc -b                                    # 타입체크
```
최초 1회, 표준사전 적재 필요: `curl -X POST http://127.0.0.1:8000/dictionary/import/standard`

## Git 원격
- origin: https://github.com/eunylee/db-toolkit.git (main 브랜치, 푸시 완료)
- ⚠️ 이 macOS 계정은 `~/.config`, `~/.zshrc`가 root 소유라 `gh`가 기본 경로에 로그인 정보를 저장 못 함.
  해결: `GH_CONFIG_DIR=~/.gh-config` 사용 (gh auth login/status 및 git push 전에 `export GH_CONFIG_DIR=~/.gh-config` 필요).
  영구 고치려면 사용자가 직접 `sudo chown -R dream:staff ~/.config ~/.zshrc` 실행 필요 (Claude가 임의로 sudo 실행하지 않음).

## 기타
- `samples/sample_da_schema.xlsx`, `.txt`: F-102 수동 테스트용 샘플 (실제 클라이언트가 줄 법한 자유형식 요구사항표, 열 개수가 행마다 달라 ragged-row 처리도 같이 확인 가능). git 추적됨.
- `engine/requirements.txt`에 `python-multipart` 누락돼 있던 것 발견/수정 (UploadFile에 실제로 필요한 의존성인데 로컬 venv엔 이미 깔려있어서 안 드러났었음).

## 확인이 필요했던 결정 (히스토리)
- 2026-07-31: F-101 시드 데이터 출처 → 사용자가 실제 행안부 CSV 직접 제공(위 참고).
- 2026-07-31: GitHub 원격 연결 → https://github.com/eunylee/db-toolkit (위 Git 원격 섹션 참고).
- 2026-07-31: F-102 헤더 강제 여부 → 자유 그리드 유지, 구조화된 컬럼은 별도 "테이블 설계" 화면으로 분리 (위 아키텍처 결정 참고).
- 2026-07-31: PK/FK/ERD 스코프 → PK는 단일 테이블 체크박스, FK/관계선은 필수 스코프 밖이며 그린필드는 수동 드래그·레거시는 자동 파싱으로 분리 (위 아키텍처 결정 참고). 수동 관계선 인터랙션은 드래그 연결 방식으로 결정(폼 방식 대신).
