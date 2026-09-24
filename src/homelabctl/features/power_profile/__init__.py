"""Automatic AC/battery power-profile feature."""

from homelabctl.features.power_profile.apply import (
    build_apply_transaction,
)
from homelabctl.features.power_profile.inspect import (
    PowerProfileAssessment,
    PowerProfilePolicy,
    assess,
)
from homelabctl.features.power_profile.plan import (
    SERVICE_PATH,
    SCRIPT_PATH,
    UDEV_RULE_PATH,
    build_power_profile_plan,
)
from homelabctl.features.power_profile.verify import (
    verify,
)

__all__ = [
    "PowerProfileAssessment",
    "PowerProfilePolicy",
    "SERVICE_PATH",
    "SCRIPT_PATH",
    "UDEV_RULE_PATH",
    "assess",
    "build_apply_transaction",
    "build_power_profile_plan",
    "verify",
]
