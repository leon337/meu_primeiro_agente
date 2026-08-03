from pathlib import Path
from typing import Any


class UnsafePathError(ValueError):
    """O caminho pedido escaparia da pasta autorizada."""


def resolve_safe_path(base: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str):
        raise TypeError("path deve ser texto")
    requested = Path(relative_path)
    if requested.is_absolute() or ".." in requested.parts:
        raise UnsafePathError("Caminho absoluto e '..' não são permitidos")
    base = base.resolve()
    target = (base / requested).resolve()
    if not target.is_relative_to(base):
        raise UnsafePathError("Acesso fora da pasta autorizada")
    if not target.is_dir():
        raise ValueError("A pasta solicitada não existe")
    return target


def list_files(base: Path, path: str = ".") -> dict[str, Any]:
    target = resolve_safe_path(base, path)
    entries = []
    for item in sorted(target.iterdir(), key=lambda entry: entry.name.casefold()):
        # Não segue links nem lê conteúdo de arquivos.
        kind = "link" if item.is_symlink() else "directory" if item.is_dir() else "file"
        size = item.stat(follow_symlinks=False).st_size if kind != "directory" else 0
        entries.append({"name": item.name, "type": kind, "size_bytes": size})
    return {"path": str(target.relative_to(base.resolve()) or "."), "entries": entries}

