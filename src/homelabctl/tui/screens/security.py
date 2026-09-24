"""Platform security inspection screen."""

from homelabctl.tui.screens.base import ModuleScreen


class SecurityScreen(ModuleScreen):
    MODULE = "security"
    SCREEN_TITLE = "Platform Security"
