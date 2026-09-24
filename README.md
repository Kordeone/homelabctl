# HomeLabCTL

HomeLabCTL is a terminal-based home-lab inspection and configuration system
for Linux servers.

The project separates read-only system inspection from privileged changes:

- `homelabctl` — normal-user CLI/TUI frontend
- `homelabd` — persistent read-only backend
- `homelabctl-apply` — constrained privileged apply helper

HomeLabCTL models configuration as **Desired**, **Recorded**, and **Actual**
state. Actual host state remains authoritative, and drift is reported rather
than silently corrected.

## Current development areas

The repository currently includes inspection and configuration components for:

- SSH
- nftables firewall
- headless operation
- power profiles
- graphics configuration
- encryption and security inspection
- storage, network, and system state

High-risk SSH and firewall changes use timed rollback protection so an
unconfirmed change can automatically restore the previous configuration.

## Requirements

- Linux
- Python 3.11 or newer
- systemd
- supported system utilities for the features being inspected or configured

The current development and deployment target is Debian-based Linux.

## Development setup

Create a virtual environment and install the project with development
dependencies:

`python3 -m venv .venv`

`.venv/bin/pip install -e '.[dev]'`

Run the test suite:

`.venv/bin/python -m pytest`

Run the frontend:

`.venv/bin/homelabctl`

## Documentation

Detailed architecture, security, backend, rollback, TUI, and feature
documentation is available under `docs/`.

## Status

HomeLabCTL is currently pre-release software. Configuration-changing features
should be tested carefully on non-critical systems before wider use.

## License

HomeLabCTL is licensed under the GNU General Public License version 3 only
(`GPL-3.0-only`). See `LICENSE`.
