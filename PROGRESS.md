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
- **도메인(Domain)은 용어(Term)와 분리된 독립 엔티티다.** 처음엔 "미등록 단어 등록 폼에 타입 필드만 추가"하려 했으나, 실데이터 확인 결과 13,176개 용어가 단 123개 도메인코드만 재사용(예: `명V100`이 1,117회, `연월일C8`이 1,850회)하는 구조라 용어마다 도메인을 새로 만들면 안 됨. 그래서 `domains` 테이블을 새로 만들고 `dictionary_terms.domain_code`와 조인해 사용횟수를 계산.
  - 표준 도메인: 표준사전 임포트(`POST /dictionary/import/standard`) 시 `derive_domains_from_terms`로 자동 추출/갱신 (읽기 전용, API로 수정·삭제 불가 → 400)
  - 커스텀 도메인: 별도 CRUD(`POST/GET/PUT/DELETE /domains`), UI에서도 표준 도메인 행에는 수정/삭제 버튼 자체가 없음
  - "출처"(표준/커스텀) 구분은 사전(dictionary_terms)과 동일한 패턴 재사용
- **도메인 선택 UI는 두 자리에서 재사용된다**: (1) 독립 "도메인 관리" 화면(목록/검색/생성/수정/삭제), (2) 테이블 설계 화면의 컬럼 "데이터타입" 칸을 누르면 뜨는 `DomainPickerModal` 팝업(검색해서 선택 또는 그 자리에서 새로 만들어 바로 선택) — 둘 다 `features/domains/ui/DomainList.tsx`를 공유.
- **미등록 단어 → 사전 등록 흐름**: 세그먼터가 "미등록"으로 표시한 구간마다 "사전에 추가" 버튼 → `AddTermModal`(물리명 입력 + `DomainPickerModal`로 도메인 선택) → `POST /dictionary/terms`(단건 upsert, source는 항상 custom으로 강제)로 등록 → 그 컬럼만 다시 `POST /naming/suggest` 호출해 제안 갱신. 실브라우저 E2E로 "VIP고객명"의 미등록 "VIP"를 등록하니 즉시 완전매칭(VIP_CUST_NM)으로 바뀌는 것까지 확인.

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
- [x] Unit 3.5: 도메인 관리 + 미등록 단어 사전 등록 (F-103 보완, Unit 3 직후 진행)
  - `app/models/domains.py`(Domain), `core/domains/derive.py`(표준사전에서 domain_code 중복제거로 도메인 추출), `core/domains/repository.py`(표준=전체재적재/읽기전용, 커스텀=CRUD, `dictionary_terms` JOIN으로 usage_count 계산)
  - `core/dictionary/repository.py`에 `upsert_term` 추가 (단건 등록/수정, replace_terms와 달리 같은 source의 다른 단어를 안 지움)
  - `api/domains.py`: GET·POST /domains, PUT·DELETE /domains/{id} (표준 도메인 수정/삭제 시 400) / `api/dictionary.py`에 POST /dictionary/terms 추가 (표준사전 임포트 시 도메인도 함께 갱신)
  - 백엔드 테스트 26개 추가 → 전체 94 passed
  - `ui/features/domains/`: model(types.ts, formatDomainType)/api/ui(DomainList, DomainForm, DomainManagerPage, DomainPickerModal, useDomainSearch 훅) — 독립 도메인 관리 화면 + 테이블 설계 컬럼의 "도메인 지정" 버튼에서 뜨는 재사용 팝업
  - `ui/features/dictionary/`: AddTermModal — TableDesigner의 "미등록: X" 경고 옆 "사전에 추가" 버튼에서 열림, 물리명 입력 + DomainPickerModal로 도메인 선택 후 등록, 등록 즉시 해당 컬럼만 제안 재조회
  - 프런트 테스트 19개 추가 → 전체 43 passed, 타입체크 통과
  - 실브라우저 E2E: 표준사전 임포트 시 123개 도메인 자동 생성(사용횟수 정확) 확인, 테이블 설계에서 도메인 피커로 컬럼 타입 지정 확인, 커스텀 도메인 생성/수정/삭제 확인, 표준 도메인은 UI에 수정/삭제 버튼 자체가 안 뜨는 것 확인, "VIP고객명"의 미등록 "VIP"를 사전에 등록하니 즉시 물리명이 VIP_CUST_NM으로 자동완성되는 것까지 확인

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
- 2026-08-03: 도메인 관리 → 독립 화면(목록/생성/수정/삭제) + 테이블 설계 컬럼에서 팝업으로도 재사용, "출처"(표준/커스텀) 구분 도입 (위 아키텍처 결정 참고). 이후 사용자가 자리 비운 동안은 확인 없이 판단해서 진행하도록 지시받음 — 미등록 단어 등록 흐름까지 이어서 마무리함.
