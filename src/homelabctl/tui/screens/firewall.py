"""Firewall inspection screen."""

from homelabctl.tui.screens.base import ModuleScreen


class FirewallScreen(ModuleScreen):
    MODULE = "firewall"
    SCREEN_TITLE = "Firewall"
