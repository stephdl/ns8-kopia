#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""Enrollment scripts of a machine. They hold its password only right after it is created or reset."""

import os
import kopia_module as km

WINDOWS_SCRIPT = """# Kopia enrollment of {name}
# Run it in the session of the user who owns the files, not as administrator.
$ErrorActionPreference = "Stop"
$kopia = "$env:LOCALAPPDATA\\Programs\\KopiaUI\\resources\\server\\kopia.exe"
if (-not (Test-Path $kopia)) {{
    winget install -e --id Kopia.KopiaUI --silent --accept-package-agreements --accept-source-agreements
}}
$env:KOPIA_PASSWORD = "{password}"
try {{
    & $kopia repository connect server `
        --url "{url}" `
        --server-cert-fingerprint "{fingerprint}" `
        --override-username "{user}" `
        --override-hostname "{machine}"
    if ($LASTEXITCODE -ne 0) {{ throw "kopia repository connect failed" }}
}} finally {{
    Remove-Item Env:KOPIA_PASSWORD -ErrorAction SilentlyContinue
}}
foreach ($folder in @("Documents", "Desktop", "Pictures")) {{
    $path = Join-Path $env:USERPROFILE $folder
    if (Test-Path $path) {{ & $kopia snapshot create $path }}
}}
# KopiaUI runs the scheduled snapshots while it stays in the tray
Start-Process "$env:LOCALAPPDATA\\Programs\\KopiaUI\\KopiaUI.exe"
"""

UNIX_SCRIPT = """#!/bin/sh
# Kopia enrollment of {name}
# Run it as the user who owns the files. Install kopia first: https://kopia.io/docs/installation/
set -e
command -v kopia >/dev/null || {{ echo "kopia is not installed" >&2; exit 1; }}
KOPIA_PASSWORD='{password}' kopia repository connect server \\
    --url='{url}' \\
    --server-cert-fingerprint='{fingerprint}' \\
    --override-username='{user}' \\
    --override-hostname='{machine}'
kopia snapshot create "$HOME"
if [ "$(uname)" = "Darwin" ]; then
    echo "Start KopiaUI and keep it running: it takes the scheduled snapshots."
elif [ "{interval}" = "0" ]; then
    echo "Manual snapshots only: no timer installed. Run: kopia snapshot create ~"
elif command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
    # Without KopiaUI, a user timer takes the snapshots
    mkdir -p "$HOME/.config/systemd/user"
    cat > "$HOME/.config/systemd/user/kopia-snapshot.service" <<UNIT
[Unit]
Description=Kopia snapshot of the home directory

[Service]
Type=oneshot
# The home directory is named on purpose: --all finds nothing in a new repository after a server restore
ExecStart=$(command -v kopia) snapshot create "$HOME"
UNIT
    cat > "$HOME/.config/systemd/user/kopia-snapshot.timer" <<UNIT
[Unit]
Description=Kopia snapshot every {interval} hours

[Timer]
OnCalendar=0/{interval}:00
RandomizedDelaySec=15min
Persistent=true

[Install]
WantedBy=timers.target
UNIT
    systemctl --user daemon-reload
    systemctl --user enable --now kopia-snapshot.timer
    echo "Snapshots scheduled every {interval} hours by kopia-snapshot.timer"
fi
"""


def enrollment(client, password):
    values = {
        "name": client["name"],
        "user": client["username"],
        "machine": client["hostname"],
        "url": f"https://{os.environ['TRAEFIK_HOST']}:{os.environ['CLIENT_PORT']}",
        "fingerprint": km.cert_fingerprint(),
        "interval": km.read_settings()["snapshot_interval"],
        # Without a password the script cannot connect: the UI offers a reset instead
        "password": password or "PASSWORD-SHOWN-ONLY-ONCE",
    }
    return {"name": values["name"], "url": values["url"], "fingerprint": values["fingerprint"],
            "username": values["user"], "hostname": values["machine"], "password": password or "",
            "powershell": WINDOWS_SCRIPT.format(**values), "shell": UNIX_SCRIPT.format(**values)}
