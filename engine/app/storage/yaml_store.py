"""Git diff 친화적인 선언형 YAML 모델 파일 read/write.

줄 단위 정렬을 유지하기 위해 key 순서를 보존하고(sort_keys=False),
블록 스타일(default_flow_style=False)로 저장한다.
"""

from pathlib import Path
from typing import Any

import yaml


def read_yaml(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def write_yaml(path: Path | str, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
