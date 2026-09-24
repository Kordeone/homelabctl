"""HomeLabCTL configuration support."""

from homelabctl.config.defaults import (
    DEFAULT_SYSTEM_CONFIG_PATH,
    DEFAULT_USER_CONFIG_PATH,
    default_config,
)
from homelabctl.config.loader import load_config
from homelabctl.config.managed import (
    DEFAULT_MANAGED_STATE_PATH,
    ManagedFeature,
    ManagedState,
    load_managed_state,
    save_managed_state,
    set_feature,
)
from homelabctl.config.schema import (
    AppConfig,
    AuditConfig,
    BackendConfig,
    UIConfig,
)

__all__ = [
    "AppConfig",
    "AuditConfig",
    "BackendConfig",
    "DEFAULT_MANAGED_STATE_PATH",
    "DEFAULT_SYSTEM_CONFIG_PATH",
    "DEFAULT_USER_CONFIG_PATH",
    "ManagedFeature",
    "ManagedState",
    "UIConfig",
    "default_config",
    "load_config",
    "load_managed_state",
    "save_managed_state",
    "set_feature",
]
