"""Loop autônomo local, limitado por ciclos, política e parada de emergência."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Event
from typing import Callable

from app.missions.models import Mission, MissionStatus, MissionStep, StepStatus
from app.missions.service import MissionService


Executor = Callable[[Mission, MissionStep], dict[str, object]]


@dataclass(slots=True)
class WorkerStats:
    cycles: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    waiting_human: int = 0


class AutonomousWorker:
    def __init__(
        self,
        service: MissionService,
        executors: dict[str, Executor],
        poll_interval: float = 2.0,
        max_steps_per_cycle: int = 10,
    ) -> None:
        self.service = service
        self.executors = executors
        self.poll_interval = poll_interval
        self.max_steps_per_cycle = max_steps_per_cycle
        self.stop_event = Event()
        self.stats = WorkerStats()

    def run_mission(self, mission_id: str) -> WorkerStats:
        mission = self.service.repository.get_mission(mission_id)
        if mission.status == MissionStatus.READY:
            mission = self.service.transition(mission_id, MissionStatus.RUNNING)
        if mission.status != MissionStatus.RUNNING:
            raise RuntimeError(f"Missão não executável: {mission.status}")
        processed = 0
        for step in self.service.repository.list_steps(mission_id):
            if self.stop_event.is_set() or processed >= self.max_steps_per_cycle:
                break
            current_mission = self.service.repository.get_mission(mission_id)
            if current_mission.emergency_stopped:
                break
            if step.status not in {StepStatus.PENDING, StepStatus.BLOCKED}:
                continue
            executor = self.executors.get(step.capability)
            if executor is None:
                self.stats.failed_steps += 1
                continue
            result = self.service.execute_step(step.step_id, executor)
            processed += 1
            if result.status == StepStatus.COMPLETED:
                self.stats.completed_steps += 1
            elif result.status == StepStatus.WAITING_HUMAN:
                self.stats.waiting_human += 1
                break
            elif result.status in {StepStatus.FAILED, StepStatus.BLOCKED}:
                self.stats.failed_steps += 1
                break
        self.stats.cycles += 1
        self._finish_if_complete(mission_id)
        return self.stats

    def run_forever(self, mission_ids: Callable[[], list[str]]) -> None:
        while not self.stop_event.is_set():
            for mission_id in mission_ids():
                if self.stop_event.is_set():
                    break
                try:
                    self.run_mission(mission_id)
                except RuntimeError:
                    continue
            self.stop_event.wait(self.poll_interval)

    def stop(self) -> None:
        self.stop_event.set()

    def _finish_if_complete(self, mission_id: str) -> None:
        mission = self.service.repository.get_mission(mission_id)
        steps = self.service.repository.list_steps(mission_id)
        if steps and all(step.status == StepStatus.COMPLETED for step in steps) and mission.status == MissionStatus.RUNNING:
            self.service.transition(mission_id, MissionStatus.COMPLETED)
