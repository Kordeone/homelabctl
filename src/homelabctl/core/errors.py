"""Exception hierarchy used throughout HomeLabCTL."""


class HomeLabError(Exception):
    """Base exception for HomeLabCTL."""


class ValidationError(HomeLabError):
    """Raised when internal or user-provided data is invalid."""


class CapabilityError(HomeLabError):
    """Raised when an operation requires an unavailable capability."""


class PlanningError(HomeLabError):
    """Raised when a valid change plan cannot be created."""


class ExecutionError(HomeLabError):
    """Raised when an apply operation fails."""


class VerificationError(HomeLabError):
    """Raised when post-change verification fails."""


class RollbackError(HomeLabError):
    """Raised when rollback preparation or execution fails."""


class BackendError(HomeLabError):
    """Raised for communication or backend-state failures."""
