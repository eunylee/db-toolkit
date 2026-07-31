# da-toolkit

프리랜서 DA 1인용 로컬 데이터 설계 툴.
- 엔진: Python (FastAPI, localhost 전용)
- 화면: React + TypeScript
- 패키징: Tauri (추후)
- 저장: SQLite + YAML (Git 버전관리 대상)

## 우선순위
필수 9개 기능(F-101~301)만 먼저 구현. 선택/제외 기능은 건드리지 않는다.
자세한 스코프는 /docs/기능정의서.docx, 개발 순서는 /docs/PRD_v4.0.docx 6장 참고.

## 원칙
- 엔진(로직)과 화면(UI)을 분리한다. 로직은 FastAPI 엔드포인트로, 화면은 그걸 호출만 한다.
- ERD 표기법은 Barker/IE 토글 가능하게 (참고: /docs/erd_notation_prototype.jsx)