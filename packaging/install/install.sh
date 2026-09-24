set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this installer with sudo."
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INSTALL_ROOT="/opt/homelabctl"
SOURCE_ROOT="$INSTALL_ROOT/source"
VENV_ROOT="$INSTALL_ROOT/venv"
SERVICE_SOURCE="$PROJECT_ROOT/packaging/systemd/homelabd.service"
SERVICE_TARGET="/etc/systemd/system/homelabd.service"
TMPFILES_SOURCE="$PROJECT_ROOT/packaging/tmpfiles/homelabd.conf"
TMPFILES_TARGET="/etc/tmpfiles.d/homelabd.conf"

TARGET_USER="${SUDO_USER:-}"

echo "Installing HomeLabCTL..."

if ! getent group homelabctl >/dev/null 2>&1; then
    groupadd --system homelabctl
fi

if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
    usermod -aG homelabctl "$TARGET_USER"
fi

rm -rf "$SOURCE_ROOT"

install -d \
    -o root \
    -g root \
    -m 0755 \
    "$INSTALL_ROOT" \
    "$SOURCE_ROOT"

cp -a \
    "$PROJECT_ROOT/src" \
    "$PROJECT_ROOT/pyproject.toml" \
    "$SOURCE_ROOT/"

chown -R root:root "$SOURCE_ROOT"
chmod -R go-w "$SOURCE_ROOT"

if [ ! -x "$VENV_ROOT/bin/python" ]; then
    python3 -m venv "$VENV_ROOT"
fi

"$VENV_ROOT/bin/python" -m pip install \
    --upgrade pip

"$VENV_ROOT/bin/python" -m pip install \
    --upgrade "$SOURCE_ROOT"

install \
    -o root \
    -g root \
    -m 0644 \
    "$SERVICE_SOURCE" \
    "$SERVICE_TARGET"

install \
    -o root \
    -g root \
    -m 0644 \
    "$TMPFILES_SOURCE" \
    "$TMPFILES_TARGET"

ln -sfn \
    "$VENV_ROOT/bin/homelabctl" \
    /usr/local/bin/homelabctl

ln -sfn \
    "$VENV_ROOT/bin/homelabd" \
    /usr/local/bin/homelabd

ln -sfn \
    "$VENV_ROOT/bin/homelabctl-apply" \
    /usr/local/bin/homelabctl-apply

systemd-tmpfiles --create \
    "$TMPFILES_TARGET"

systemctl daemon-reload
systemctl enable homelabd.service
systemctl restart homelabd.service

echo
echo "HomeLabCTL installed."
echo

if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
    echo "User '$TARGET_USER' was added to the homelabctl group."
    echo "Log out and back in before using the backend socket."
fi
