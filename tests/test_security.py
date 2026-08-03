from pathlib import Path
import pytest

from app.tools.files import UnsafePathError, list_files
from app.tools.registry import ToolError, ToolRegistry


def test_parent_traversal_is_blocked(tmp_path: Path) -> None:
    with pytest.raises(UnsafePathError):
        list_files(tmp_path, "../")


def test_absolute_path_is_blocked(tmp_path: Path) -> None:
    with pytest.raises(UnsafePathError):
        list_files(tmp_path, "/tmp")


def test_unknown_tool_is_blocked(tmp_path: Path) -> None:
    with pytest.raises(ToolError, match="não autorizada"):
        ToolRegistry(tmp_path).execute("exec", {"command": "echo oi"})


def test_invalid_parameters_are_blocked(tmp_path: Path) -> None:
    with pytest.raises(ToolError, match="Parâmetros inválidos"):
        ToolRegistry(tmp_path).execute("get_system_info", {"unexpected": True})


def test_non_object_parameters_are_blocked(tmp_path: Path) -> None:
    with pytest.raises(ToolError, match="objeto"):
        ToolRegistry(tmp_path).execute("list_files", "../")  # type: ignore[arg-type]

