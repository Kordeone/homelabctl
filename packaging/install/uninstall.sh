set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this uninstaller with sudo."
    exit 1
fi

echo "Removing HomeLabCTL runtime installation..."

systemctl disable --now homelabd.service \
    2>/dev/null || true

rm -f \
    /etc/systemd/system/homelabd.service \
    /etc/tmpfiles.d/homelabd.conf \
    /usr/local/bin/homelabctl \
    /usr/local/bin/homelabd \
    /usr/local/bin/homelabctl-apply

rm -rf \
    /run/homelabd \
    /opt/homelabctl

systemctl daemon-reload

echo
echo "HomeLabCTL runtime removed."
echo "System configurations managed by HomeLabCTL were NOT removed."
echo "The homelabctl system group was also preserved."
