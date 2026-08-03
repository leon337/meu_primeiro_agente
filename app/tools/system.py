from typing import Any
import platform


def get_system_info() -> dict[str, Any]:
    return {"operating_system": platform.system(), "system_version": platform.version(), "architecture": platform.machine(), "computer_name": platform.node(), "python_version": platform.python_version()}

