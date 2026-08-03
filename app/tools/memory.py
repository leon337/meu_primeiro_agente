from typing import Any
import psutil

from app.tools.disk import bytes_to_gib


def get_memory_usage() -> dict[str, Any]:
    memory = psutil.virtual_memory()
    return {"total_gib": bytes_to_gib(memory.total), "used_gib": bytes_to_gib(memory.used), "available_gib": bytes_to_gib(memory.available), "percent_used": round(float(memory.percent), 1)}

