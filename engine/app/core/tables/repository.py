"""테이블 설계 모델의 YAML 저장소.

실제 사용 시에는 클라이언트 프로젝트 폴더의 model.yaml이 그 프로젝트의 git 저장소에서
버전관리된다(CLAUDE.md 방침). 지금은 Tauri 패키징 전이라 워크스페이스 폴더 선택 UI가 없으므로,
개발용 기본 워크스페이스 경로를 로컬 런타임 상태로 취급한다(SQLite와 동일하게 git 비대상).
"""

from pathlib import Path

from app.models.tables import Table
from app.storage import yaml_store

DEFAULT_WORKSPACE_MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "workspace" / "model.yaml"


def load_tables(path: Path | str | None = None) -> list[Table]:
    data = yaml_store.read_yaml(path or DEFAULT_WORKSPACE_MODEL_PATH)
    return [Table(**t) for t in data.get("tables", [])]


def save_table(table: Table, path: Path | str | None = None) -> Table:
    path = path or DEFAULT_WORKSPACE_MODEL_PATH
    tables = [t for t in load_tables(path) if t.logical_name != table.logical_name]
    tables.append(table)
    yaml_store.write_yaml(path, {"tables": [t.model_dump(mode="json") for t in tables]})
    return table


def get_table(logical_name: str, path: Path | str | None = None) -> Table | None:
    return next((t for t in load_tables(path) if t.logical_name == logical_name), None)
