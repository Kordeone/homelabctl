"""SSH feature constants."""

MANAGED_SSH_FILENAME = "00-homelabctl.conf"

MANAGED_SSH_DIRECTORY = (
    "/etc/ssh/sshd_config.d"
)

MANAGED_SSH_PATH = (
    f"{MANAGED_SSH_DIRECTORY}/"
    f"{MANAGED_SSH_FILENAME}"
)

# No pre-release legacy managed filenames are retained.
LEGACY_MANAGED_SSH_FILENAMES: tuple[str, ...] = ()
LEGACY_MANAGED_SSH_PATHS: tuple[str, ...] = ()
