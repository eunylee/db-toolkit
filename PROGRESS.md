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

## 다음 (우선순위 순, 기능정의서 6장 기준)
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

## Git 원격
- origin: https://github.com/eunylee/db-toolkit.git (main 브랜치, 푸시 완료)
- ⚠️ 이 macOS 계정은 `~/.config`, `~/.zshrc`가 root 소유라 `gh`가 기본 경로에 로그인 정보를 저장 못 함.
  해결: `GH_CONFIG_DIR=~/.gh-config` 사용 (gh auth login/status 및 git push 전에 `export GH_CONFIG_DIR=~/.gh-config` 필요).
  영구 고치려면 사용자가 직접 `sudo chown -R dream:staff ~/.config ~/.zshrc` 실행 필요 (Claude가 임의로 sudo 실행하지 않음).

## 확인이 필요했던 결정 (히스토리)
- 2026-07-31: F-101 시드 데이터 출처 → 사용자가 실제 행안부 CSV 직접 제공(위 참고).
- 2026-07-31: GitHub 원격 연결 → https://github.com/eunylee/db-toolkit (위 Git 원격 섹션 참고).
