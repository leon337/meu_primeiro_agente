"""Máquinas de estado fechadas para missões e etapas."""

from app.missions.models import MissionStatus, StepStatus


class InvalidTransition(ValueError):
    pass


MISSION_TRANSITIONS: dict[MissionStatus, set[MissionStatus]] = {
    MissionStatus.CREATED: {MissionStatus.PLANNING, MissionStatus.CANCELLED},
    MissionStatus.PLANNING: {MissionStatus.READY, MissionStatus.BLOCKED, MissionStatus.CANCELLED},
    MissionStatus.READY: {MissionStatus.RUNNING, MissionStatus.CANCELLED, MissionStatus.BLOCKED},
    MissionStatus.RUNNING: {
        MissionStatus.WAITING_HUMAN,
        MissionStatus.BLOCKED,
        MissionStatus.RECOVERING,
        MissionStatus.COMPLETED,
        MissionStatus.FAILED,
        MissionStatus.CANCELLED,
    },
    MissionStatus.WAITING_HUMAN: {
        MissionStatus.RUNNING,
        MissionStatus.BLOCKED,
        MissionStatus.CANCELLED,
        MissionStatus.FAILED,
    },
    MissionStatus.BLOCKED: {MissionStatus.RECOVERING, MissionStatus.CANCELLED, MissionStatus.FAILED},
    MissionStatus.RECOVERING: {MissionStatus.RUNNING, MissionStatus.BLOCKED, MissionStatus.FAILED, MissionStatus.CANCELLED},
    MissionStatus.COMPLETED: set(),
    MissionStatus.FAILED: set(),
    MissionStatus.CANCELLED: set(),
}

STEP_TRANSITIONS: dict[StepStatus, set[StepStatus]] = {
    StepStatus.PENDING: {StepStatus.RUNNING, StepStatus.WAITING_HUMAN, StepStatus.BLOCKED, StepStatus.CANCELLED},
    StepStatus.RUNNING: {
        StepStatus.COMPLETED,
        StepStatus.FAILED,
        StepStatus.WAITING_HUMAN,
        StepStatus.BLOCKED,
        StepStatus.CANCELLED,
    },
    StepStatus.WAITING_HUMAN: {StepStatus.PENDING, StepStatus.RUNNING, StepStatus.BLOCKED, StepStatus.CANCELLED},
    StepStatus.BLOCKED: {StepStatus.RUNNING, StepStatus.FAILED, StepStatus.CANCELLED},
    StepStatus.COMPLETED: set(),
    StepStatus.FAILED: set(),
    StepStatus.CANCELLED: set(),
}


def validate_mission_transition(current: MissionStatus, target: MissionStatus) -> None:
    if target not in MISSION_TRANSITIONS[current]:
        raise InvalidTransition(f"Transição de missão inválida: {current} → {target}")


def validate_step_transition(current: StepStatus, target: StepStatus) -> None:
    if target not in STEP_TRANSITIONS[current]:
        raise InvalidTransition(f"Transição de etapa inválida: {current} → {target}")
