"""Central Jinja template renderer for managed features."""

from __future__ import annotations

from typing import Any

from jinja2 import (
    Environment,
    PackageLoader,
    StrictUndefined,
)


_environment = Environment(
    loader=PackageLoader(
        "homelabctl",
        "templates",
    ),
    undefined=StrictUndefined,
    autoescape=False,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_template(
    template_name: str,
    **context: Any,
) -> str:
    template = _environment.get_template(
        template_name
    )

    return template.render(
        **context
    )
