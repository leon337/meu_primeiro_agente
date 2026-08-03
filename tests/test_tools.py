from pathlib import Path
from unittest.mock import patch

from app.tools.disk import bytes_to_gib, get_disk_space
from app.tools.memory import get_memory_usage
from app.tools.registry import ToolRegistry
from app.tools.system import get_system_info


def test_bytes_to_gib_and_disk_calculation() -> None:
    assert bytes_to_gib(2 * 1024**3) == 2.0
    with patch("app.tools.disk.shutil.disk_usage", return_value=(100, 25, 75)):
        result = get_disk_space(Path("."))
    assert result["percent_used"] == 25.0
    assert set(result) == {"total_gib", "used_gib", "free_gib", "percent_used"}


def test_memory_usage() -> None:
    with patch("app.tools.memory.psutil.virtual_memory") as memory:
        memory.return_value.total = 8 * 1024**3
        memory.return_value.used = 3 * 1024**3
        memory.return_value.available = 5 * 1024**3
        memory.return_value.percent = 37.5
        result = get_memory_usage()
    assert result == {"total_gib": 8.0, "used_gib": 3.0, "available_gib": 5.0, "percent_used": 37.5}


def test_system_info_has_expected_fields() -> None:
    assert set(get_system_info()) == {"operating_system", "system_version", "architecture", "computer_name", "python_version"}


def test_registry_definitions_and_execution(tmp_path: Path) -> None:
    registry = ToolRegistry(tmp_path)
    assert {tool.name for tool in registry.definitions} == {"get_disk_space", "get_memory_usage", "get_system_info", "list_files"}
    assert "python_version" in registry.execute("get_system_info")


def test_list_files_returns_metadata_only(tmp_path: Path) -> None:
    (tmp_path / "exemplo.txt").write_text("segredo", encoding="utf-8")
    result = ToolRegistry(tmp_path).execute("list_files", {"path": "."})
    assert result["entries"] == [{"name": "exemplo.txt", "type": "file", "size_bytes": 7}]
    assert "segredo" not in str(result)

