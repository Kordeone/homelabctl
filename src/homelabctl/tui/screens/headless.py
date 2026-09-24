"""Headless configuration inspection screen."""

from homelabctl.tui.screens.base import ModuleScreen


class HeadlessScreen(ModuleScreen):
    MODULE = "headless"
    SCREEN_TITLE = "Headless / Sleep Policy"
