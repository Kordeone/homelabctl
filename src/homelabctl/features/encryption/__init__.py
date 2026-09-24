"""Disk-encryption inspection and guided management."""

from homelabctl.features.encryption.capabilities import (
    EncryptionCapabilities,
    detect_capabilities,
)
from homelabctl.features.encryption.inspect import (
    EncryptionAssessment,
    assess,
)
from homelabctl.features.encryption.plan import (
    build_tpm_enrollment_plan,
)
from homelabctl.features.encryption.verify import (
    verify_luks,
)

__all__ = [
    "EncryptionAssessment",
    "EncryptionCapabilities",
    "assess",
    "build_tpm_enrollment_plan",
    "detect_capabilities",
    "verify_luks",
]
