#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""Enrollment scripts of a machine. They hold its password only right after it is created or reset."""

import os
import kopia_module as km

# The scripts are pasted in a terminal. Each one is a single block, so a failure skips the rest
# without closing the terminal: no exit, no set -e. Unix blocks hold no comment, because zsh,
# the macOS shell, runs a pasted "#" line as a command. A failure still sets the exit status.
WINDOWS_SCRIPT = """& {{
    # Kopia enrollment of {name}
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
    # The user picks the folders in KopiaUI, which then runs the scheduled snapshots from the tray
    Start-Process "$env:LOCALAPPDATA\\Programs\\KopiaUI\\KopiaUI.exe"
    Write-Host "Enrolled. Ask your administrator to add the folders to back up, then start KopiaUI."
}}
"""

UNIX_CONNECT = """KOPIA_PASSWORD='{password}' "$kopia" repository connect server \\
        --url='{url}' \\
        --server-cert-fingerprint='{fingerprint}' \\
        --override-username='{user}' \\
        --override-hostname='{machine}'"""

# KopiaUI ships its own kopia outside the PATH
UNIX_SCRIPT = """for kopia in "$(command -v kopia)" /opt/KopiaUI/resources/server/kopia \\
        /Applications/KopiaUI.app/Contents/Resources/server/kopia; do
    [ -x "$kopia" ] && break
    kopia=
done
if [ -z "$kopia" ]; then
    echo "kopia is not installed: install KopiaUI first, see https://kopia.io/docs/installation/" >&2
    false
elif """ + UNIX_CONNECT + """; then
    echo "Enrolled. Ask your administrator to add the folders to back up, then start KopiaUI."
    echo "Keep KopiaUI running: it takes the scheduled snapshots."
else
    false
fi
"""

# Without lingering, the timer stops when the user logs out
SERVER_SCRIPT = """kopia="$(command -v kopia)"
if [ -z "$kopia" ]; then
    echo "kopia is not installed: see https://kopia.io/docs/installation/" >&2
    false
elif ! """ + UNIX_CONNECT + """; then
    false
elif [ "{interval}" = "0" ]; then
    echo "Manual snapshots only: no timer installed. Run: kopia snapshot create ~"
elif command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
    mkdir -p "$HOME/.config/systemd/user" &&
    cat > "$HOME/.config/systemd/user/kopia-snapshot.service" <<UNIT &&
[Unit]
Description=Kopia snapshot of the home directory

[Service]
Type=oneshot
# The home directory is named on purpose: --all finds nothing in a new repository after a server restore
ExecStart=$kopia snapshot create "$HOME"
UNIT
    cat > "$HOME/.config/systemd/user/kopia-snapshot.timer" <<UNIT &&
[Unit]
Description=Kopia snapshot every {interval} hours

[Timer]
OnCalendar=0/{interval}:00
RandomizedDelaySec=15min
Persistent=true

[Install]
WantedBy=timers.target
UNIT
    systemctl --user daemon-reload &&
    systemctl --user enable --now kopia-snapshot.timer &&
    if ! loginctl show-user "$(id -un)" -p Linger 2>/dev/null | grep -q yes \\
            && ! loginctl enable-linger 2>/dev/null; then
        echo "Run as root: loginctl enable-linger $(id -un). Otherwise snapshots stop at logout." >&2
        false
    else
        echo "Snapshots of $HOME scheduled every {interval} hours by kopia-snapshot.timer"
    fi
else
    echo "No systemd user session: log in as this user over SSH and paste the commands again." >&2
    false
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
            "powershell": WINDOWS_SCRIPT.format(**values), "shell": UNIX_SCRIPT.format(**values),
            "server": SERVER_SCRIPT.format(**values)}
