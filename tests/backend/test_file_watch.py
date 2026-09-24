from homelabctl.backend.collectors.file_watch import (
    FileWatchCollector,
)


def test_file_watch_initial_collection():
    collector = FileWatchCollector()

    result = collector.collect()

    assert len(result.modules) == 1

    state = result.modules[0]

    assert state.module == "file_watch"
    assert state.status.value == "pass"

    assert (
        state.values[
            "changed_files"
        ].value
        == []
    )
