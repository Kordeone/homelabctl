"""Shared data models used by HomeLabCTL.

These models intentionally contain no system-changing logic. They describe
state, capabilities, plans, verification results, and audit events.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"
    UNAVAILABLE = "unavailable"
    DRIFT = "drift"
    MANUAL = "manual"


class CapabilityState(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    MANUAL = "manual"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChangeKind(str, Enum):
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    ENABLE_SERVICE = "enable_service"
    DISABLE_SERVICE = "disable_service"
    START_SERVICE = "start_service"
    STOP_SERVICE = "stop_service"
    RESTART_SERVICE = "restart_service"
    RUN_COMMAND = "run_command"
    MANUAL_ACTION = "manual_action"
    OTHER = "other"


@dataclass(slots=True)
class CapabilityResult:
    key: str
    name: str
    state: CapabilityState
    reason: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.state == CapabilityState.AVAILABLE


@dataclass(slots=True)
class StateValue:
    key: str
    value: Any = None
    source: str | None = None
    readable: bool = True
    error: str | None = None


@dataclass(slots=True)
class ModuleActualState:
    module: str
    collected_at: str
    status: Status = Status.UNKNOWN
    summary: str = ""
    values: dict[str, StateValue] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        item = self.values.get(key)
        if item is None or not item.readable:
            return default
        return item.value


@dataclass(slots=True)
class DesiredSetting:
    key: str
    value: Any
    required: bool = True
    description: str | None = None


@dataclass(slots=True)
class ModuleDesiredState:
    module: str
    settings: dict[str, DesiredSetting] = field(default_factory=dict)


@dataclass(slots=True)
class DriftItem:
    key: str
    desired: Any
    actual: Any
    matches: bool
    reason: str | None = None


@dataclass(slots=True)
class DriftReport:
    module: str
    status: Status
    items: list[DriftItem] = field(default_factory=list)

    @property
    def drift_count(self) -> int:
        return sum(1 for item in self.items if not item.matches)


@dataclass(slots=True)
class PlanStep:
    id: str
    description: str
    kind: ChangeKind
    target: str | None = None
    before: Any = None
    after: Any = None
    requires_root: bool = False
    reversible: bool = True
    command_preview: str | None = None


@dataclass(slots=True)
class ChangePlan:
    id: str
    feature: str
    title: str
    summary: str
    risk: RiskLevel
    steps: list[PlanStep] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    requires_root: bool = False
    requires_reboot: bool = False

    @property
    def empty(self) -> bool:
        return not self.steps


@dataclass(slots=True)
class ExecutionResult:
    plan_id: str
    success: bool
    message: str = ""
    completed_steps: list[str] = field(default_factory=list)
    failed_step: str | None = None
    error: str | None = None


@dataclass(slots=True)
class VerificationCheck:
    key: str
    expected: Any
    actual: Any
    passed: bool
    message: str = ""


@dataclass(slots=True)
class VerificationReport:
    feature: str
    status: Status
    checks: list[VerificationCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == Status.PASS


@dataclass(slots=True)
class RollbackAction:
    description: str
    target: str | None = None
    command_preview: str | None = None


@dataclass(slots=True)
class RollbackPlan:
    source_plan_id: str
    available: bool
    actions: list[RollbackAction] = field(default_factory=list)
    reason_unavailable: str | None = None


@dataclass(slots=True)
class AuditEvent:
    timestamp: str
    category: str
    action: str
    result: str
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def model_to_dict(value: Any) -> Any:
    """Convert supported dataclasses recursively into JSON-friendly values."""
    if isinstance(value, Enum):
        return value.value

    if hasattr(value, "__dataclass_fields__"):
        raw = asdict(value)
        return model_to_dict(raw)

    if isinstance(value, dict):
        return {
            str(key): model_to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [model_to_dict(item) for item in value]

    return value
