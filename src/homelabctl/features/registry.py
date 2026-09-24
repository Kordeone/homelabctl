"""HomeLabCTL feature registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeatureDefinition:
    key: str
    title: str
    description: str

    configurable: bool = True
    installs_runtime_service: bool = False
    default_selected: bool = False


FEATURES = {
    "ssh": FeatureDefinition(
        key="ssh",
        title="SSH",
        description="OpenSSH security configuration.",
    ),

    "firewall": FeatureDefinition(
        key="firewall",
        title="Firewall",
        description="nftables host firewall.",
    ),

    "headless": FeatureDefinition(
        key="headless",
        title="Headless",
        description=(
            "Lid and desktop idle/suspend policy."
        ),
    ),

    "graphics": FeatureDefinition(
        key="graphics",
        title="Graphics",
        description=(
            "Graphics driver and Nouveau policy."
        ),
    ),

    "security": FeatureDefinition(
        key="security",
        title="Security",
        description=(
            "Secure Boot, lockdown and TPM inspection."
        ),
        configurable=False,
    ),

    "encryption": FeatureDefinition(
        key="encryption",
        title="Encryption",
        description="LUKS and TPM/Clevis inspection.",
    ),

    "power_profile": FeatureDefinition(
        key="power_profile",
        title="Power Profile",
        description=(
            "Automatic AC/battery power profile."
        ),
        installs_runtime_service=True,
    ),

    "power_guardian": FeatureDefinition(
        key="power_guardian",
        title="Power Guardian",
        description=(
            "Battery outage protection and RTC recovery."
        ),
        installs_runtime_service=True,
    ),
}


def get_feature(
    key: str,
) -> FeatureDefinition | None:
    return FEATURES.get(key)


def all_features() -> list[FeatureDefinition]:
    return list(FEATURES.values())
