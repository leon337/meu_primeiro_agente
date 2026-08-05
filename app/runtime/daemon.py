"""Daemon local que continua missões prontas sem depender do chat."""

from __future__ import annotations

import logging
import signal

from dotenv import load_dotenv

from app.missions.models import MissionStatus
from app.runtime.executors import ExecutiveActionExecutor
from app.runtime.factory import create_runtime
from app.runtime.worker import AutonomousWorker


logger = logging.getLogger(__name__)


def main() -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    service, _ = create_runtime()
    executor = ExecutiveActionExecutor()
    worker = AutonomousWorker(
        service,
        executors={
            "observe": executor,
            "prepare": executor,
            "execute_reversible": executor,
            "communicate": executor,
            "publish": executor,
            "install": executor,
            "delete": executor,
        },
    )

    def stop_handler(signum, frame):  # type: ignore[no-untyped-def]
        logger.info("Recebido sinal %s; encerrando após a ação atual", signum)
        worker.stop()

    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    def mission_ids() -> list[str]:
        missions = service.repository.list_missions((MissionStatus.READY, MissionStatus.RUNNING))
        return [mission.mission_id for mission in missions if not mission.emergency_stopped]

    worker.run_forever(mission_ids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
