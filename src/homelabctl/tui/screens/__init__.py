"""HomeLabCTL auxiliary screens and feature views."""

from homelabctl.tui.screens.diagnostics import (
    DiagnosticsScreen,
)
from homelabctl.tui.screens.encryption import (
    EncryptionScreen,
)
from homelabctl.tui.screens.firewall import (
    FirewallScreen,
)
from homelabctl.tui.screens.graphics import (
    GraphicsScreen,
)
from homelabctl.tui.screens.headless import (
    HeadlessScreen,
)
from homelabctl.tui.screens.logs import (
    LogsScreen,
)
from homelabctl.tui.screens.network import (
    NetworkScreen,
)
from homelabctl.tui.screens.power import (
    PowerScreen,
)
from homelabctl.tui.screens.security import (
    SecurityScreen,
)
from homelabctl.tui.screens.ssh import (
    SSHView,
)
from homelabctl.tui.screens.storage import (
    StorageScreen,
)
from homelabctl.tui.screens.system import (
    SystemScreen,
)

__all__ = [
    "DiagnosticsScreen",
    "EncryptionScreen",
    "FirewallScreen",
    "GraphicsScreen",
    "HeadlessScreen",
    "LogsScreen",
    "NetworkScreen",
    "PowerScreen",
    "SSHView",
    "SecurityScreen",
    "StorageScreen",
    "SystemScreen",
]
