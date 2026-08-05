"""CLI local do runtime executivo."""

from __future__ import annotations

import argparse
import json

from app.mcf.adapter import MCFTaskRequest
from app.runtime.factory import create_runtime


def main() -> int:
    parser = argparse.ArgumentParser(description="Agente Executivo Pessoal")
    parser.add_argument("command", choices=("accept", "status", "emergency-stop"))
    parser.add_argument("value", help="JSON da missão ou identificador")
    parser.add_argument("--reason", default="Solicitação humana")
    args = parser.parse_args()
    service, adapter = create_runtime()
    if args.command == "accept":
        request = MCFTaskRequest.from_payload(json.loads(args.value))
        mission = adapter.accept(request)
        print(json.dumps({"mission_id": mission.mission_id, "status": mission.status}, ensure_ascii=False))
    elif args.command == "status":
        print(json.dumps(adapter.result_packet(args.value), ensure_ascii=False, indent=2))
    else:
        mission = service.emergency_stop(args.value, "Leandro", args.reason)
        print(json.dumps({"mission_id": mission.mission_id, "status": mission.status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
