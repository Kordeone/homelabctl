"""Platform security inspection feature."""

from homelabctl.features.security.capabilities import (
    SecurityCapabilities,
    detect_capabilities,
)
from homelabctl.features.security.inspect import (
    SecurityAssessment,
    assess,
)
from homelabctl.features.security.manual_steps import (
    ManualStep,
    get_manual_steps,
)
from homelabctl.features.security.verify import (
    verify,
)

__all__ = [
    "ManualStep",
    "SecurityAssessment",
    "SecurityCapabilities",
    "assess",
    "detect_capabilities",
    "get_manual_steps",
    "verify",
]
