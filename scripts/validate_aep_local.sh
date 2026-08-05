#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXPECTED_REMOTE="origin/integration/aep-7-phases-2.1.3"
TMP_DIR="$(mktemp -d -t aep-local-gate-XXXXXX)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

printf '\n=== AEP LOCAL GATE ===\n'
printf 'root=%s\n' "$ROOT"
printf 'head=%s\n' "$(git rev-parse HEAD)"
printf 'branch=%s\n' "$(git branch --show-current)"

if ! git rev-parse --verify "$EXPECTED_REMOTE" >/dev/null 2>&1; then
  echo "ERRO: referência $EXPECTED_REMOTE não encontrada. Execute git fetch origin."
  exit 2
fi

EXPECTED_HEAD="$(git rev-parse "$EXPECTED_REMOTE")"
CURRENT_HEAD="$(git rev-parse HEAD)"
if [[ "$CURRENT_HEAD" != "$EXPECTED_HEAD" ]]; then
  echo "ERRO: worktree não está no commit aprovado."
  echo "expected=$EXPECTED_HEAD"
  echo "current=$CURRENT_HEAD"
  exit 3
fi

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "ERRO: existem alterações rastreadas no worktree."
  git status --short
  exit 4
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-executive.txt
.venv/bin/python -m playwright install chromium

mkdir -p var/aep
chmod 700 var var/aep 2>/dev/null || true

printf '\n=== COMPILAÇÃO E TESTES ===\n'
.venv/bin/python -m compileall -q app
if command -v node >/dev/null 2>&1; then
  node --check public/app.js
else
  echo "AVISO: Node.js ausente; validação JS já foi executada no CI."
fi
.venv/bin/python -m pytest -q

printf '\n=== MISSÃO DRY-RUN, PERSISTÊNCIA E EMERGÊNCIA ===\n'
AEP_DATABASE_PATH="$TMP_DIR/aep.sqlite3" \
AEP_AUDIT_SIGNING_KEY="local-gate-signing-key" \
AEP_BROWSER_REAL=0 \
AEP_DESKTOP_REAL=0 \
.venv/bin/python - <<'PY'
from __future__ import annotations

import json
import os

from app.audit.ledger import validate_event_chain
from app.audit.receipts import verify_receipt
from app.mcf.adapter import MCFTaskRequest
from app.missions.models import MissionStatus, StepStatus
from app.runtime.executors import ExecutiveActionExecutor
from app.runtime.factory import create_runtime
from app.runtime.worker import AutonomousWorker

service, adapter = create_runtime(os.environ["AEP_DATABASE_PATH"])
request = MCFTaskRequest(
    mission_id="MCF-AEP-LOCAL-GATE-001",
    requester_agent="Mestre",
    objective="Ler o título público de example.com em modo dry-run",
    return_to="Mestre",
    allowed_domains=("example.com",),
    allowed_capabilities=("observe",),
    forbidden_actions=("submit", "download", "fill", "fill_credential"),
    completion_criteria=("plano validado", "recibo emitido"),
    max_autonomy=1,
)
first = adapter.accept(request)
second = adapter.accept(request)
assert first.mission_id == second.mission_id
service.transition(request.mission_id, MissionStatus.PLANNING)
step = adapter.add_step(
    request.mission_id,
    1,
    "read_text",
    "observe",
    "https://example.com/",
    {"selector": "h1"},
)
repeated_step = adapter.add_step(
    request.mission_id,
    1,
    "read_text",
    "observe",
    "https://example.com/",
    {"selector": "h1"},
)
assert step.step_id == repeated_step.step_id
service.transition(request.mission_id, MissionStatus.READY)
worker = AutonomousWorker(service, {"observe": ExecutiveActionExecutor()}, poll_interval=0)
stats = worker.run_mission(request.mission_id)
mission = service.repository.get_mission(request.mission_id)
stored_step = service.repository.get_step(step.step_id)
assert mission.status == MissionStatus.COMPLETED
assert stored_step.status == StepStatus.COMPLETED
assert stored_step.evidence[-1]["data"]["mode"] == "dry_run"
assert validate_event_chain(service.repository.list_events(request.mission_id))
packet = adapter.result_packet(request.mission_id)
assert verify_receipt(packet, os.environ["AEP_AUDIT_SIGNING_KEY"])

stop_request = MCFTaskRequest(
    mission_id="MCF-AEP-LOCAL-GATE-STOP",
    requester_agent="Mestre",
    objective="Validar parada de emergência",
    return_to="Mestre",
    allowed_domains=("example.com",),
    allowed_capabilities=("observe",),
    forbidden_actions=(),
    completion_criteria=("missão cancelada",),
    max_autonomy=1,
)
adapter.accept(stop_request)
service.transition(stop_request.mission_id, MissionStatus.PLANNING)
stop_step = adapter.add_step(
    stop_request.mission_id,
    1,
    "read_text",
    "observe",
    "https://example.com/",
    {"selector": "h1"},
)
service.transition(stop_request.mission_id, MissionStatus.READY)
stopped = service.emergency_stop(stop_request.mission_id, "Leandro", "Gate local")
event_count = len(service.repository.list_events(stop_request.mission_id))
repeated_stop = service.emergency_stop(stop_request.mission_id, "Leandro", "Repetição segura")
assert repeated_stop.version == stopped.version
assert len(service.repository.list_events(stop_request.mission_id)) == event_count
assert stopped.status == MissionStatus.CANCELLED
assert stopped.emergency_stopped
assert service.repository.get_step(stop_step.step_id).status == StepStatus.CANCELLED

print(json.dumps({
    "dry_run_mission": mission.status.value,
    "dry_run_completed_steps": stats.completed_steps,
    "receipt_verified": True,
    "event_chain_verified": True,
    "emergency_stop": stopped.status.value,
    "idempotency": True,
}, ensure_ascii=False, sort_keys=True))
PY

printf '\n=== PLAYWRIGHT REAL SOMENTE LEITURA ===\n'
AEP_GATE_TMP="$TMP_DIR" .venv/bin/python - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from app.browser.executor import PlaywrightBrowserExecutor
from app.browser.models import BrowserAction, BrowserOperation

root = Path(os.environ["AEP_GATE_TMP"])
executor = PlaywrightBrowserExecutor(
    ("example.com",),
    profile_directory=root / "browser-profile",
    output_directory=root / "outputs",
    dry_run=False,
    headless=True,
)
result = executor.execute([
    BrowserAction(BrowserOperation.NAVIGATE, url="https://example.com/"),
    BrowserAction(BrowserOperation.READ_TEXT, selector="h1"),
])
text = str(result["outputs"][1]["text"])
assert "Example Domain" in text
print(json.dumps({
    "mode": result["mode"],
    "completed": result["completed"],
    "read_only_text_verified": True,
}, sort_keys=True))
PY

printf '\nLOCAL_GATE_RESULT=PASS\n'
printf 'validated_head=%s\n' "$CURRENT_HEAD"
