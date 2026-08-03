from pathlib import Path
import shutil
from typing import Any


def bytes_to_gib(value: int) -> float:
    return round(value / (1024**3), 2)


def get_disk_space(path: Path = Path.cwd()) -> dict[str, Any]:
    total, used, free = shutil.disk_usage(path)
    percent = round((used / total * 100) if total else 0.0, 1)
    return {"total_gib": bytes_to_gib(total), "used_gib": bytes_to_gib(used), "free_gib": bytes_to_gib(free), "percent_used": percent}
