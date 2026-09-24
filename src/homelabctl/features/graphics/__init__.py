"""Graphics-driver management feature."""

from homelabctl.features.graphics.apply import (
    build_disable_nouveau_transaction,
)
from homelabctl.features.graphics.inspect import (
    GraphicsAssessment,
    assess,
)
from homelabctl.features.graphics.plan import (
    NOUVEAU_CONFIG,
    build_disable_nouveau_plan,
    render_nouveau_blacklist,
)
from homelabctl.features.graphics.verify import (
    verify,
)

__all__ = [
    "GraphicsAssessment",
    "NOUVEAU_CONFIG",
    "assess",
    "build_disable_nouveau_plan",
    "build_disable_nouveau_transaction",
    "render_nouveau_blacklist",
    "verify",
]
