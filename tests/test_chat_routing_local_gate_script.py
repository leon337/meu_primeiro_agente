from pathlib import Path
import py_compile


def test_local_chat_routing_gate_compiles_and_uses_real_runtime(tmp_path: Path) -> None:
    script = Path("scripts/validate_aep_chat_routing_local.py")
    py_compile.compile(str(script), cfile=str(tmp_path / "gate.pyc"), doraise=True)
    content = script.read_text(encoding="utf-8")

    assert '"aep_submit_mission"' in content
    assert '"AEP_BROWSER_REAL": "1"' in content
    assert '"AEP_BROWSER_HEADLESS": "1"' in content
    assert "secrets.token_urlsafe" in content
    assert '"evidence_text_verified"' in content
    assert "Example Domain" in content
    assert "control_token" not in content.split("print(", 1)[-1]
    assert "device_token" not in content.split("print(", 1)[-1]
