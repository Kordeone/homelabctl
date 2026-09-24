from homelabctl.backend.collectors import (
    CollectorResult,
    default_collectors,
)


def test_default_collectors_exist():
    collectors = default_collectors()

    names = {
        collector.name
        for collector in collectors
    }

    assert "system" in names
    assert "ssh" in names
    assert "firewall" in names
    assert "headless" in names
    assert "graphics" in names
    assert "security" in names
    assert "encryption" in names
    assert "power" in names
    assert "network" in names
    assert "storage" in names
    assert "file_watch" in names


def test_collector_result_defaults():
    result = CollectorResult()

    assert result.modules == []
    assert result.capabilities == []
