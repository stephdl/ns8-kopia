# User guide

This guide is for the person who uses a machine backed up to the Kopia server. Your
administrator gives you an enrollment script and this page.

Your machine backs up to the server by itself, at a fixed interval, while Kopia runs. You
only see your own backups. Nobody else using the server can see them, except the
administrator.

## Run the enrollment script

Run the script once, logged in as yourself, in your own session. Do not run it as
administrator, root or SYSTEM: the backup would be set up for another account and you would
see nothing.

- **Windows**: open PowerShell (not as administrator), paste the script and press Enter. The
  script installs KopiaUI when it is missing.
- **Linux and macOS**: open a terminal, paste the script and press Enter. If your shell is
  fish, type `sh` first, then paste.

The script holds a password. Delete it after use and never send it to anyone. Anyone who has
it can read your backups. The password also stays in the history of your terminal. If someone
else may have read it, ask your administrator to reset it.

## Keep KopiaUI running

On a desktop, KopiaUI takes the backups. No KopiaUI, no backup.

KopiaUI lives in the tray, the small icons next to the clock. After the enrollment it starts
hidden: click its icon to open it. In the icon menu, pick **Launch At Startup**, so it starts
again after each login. On Windows the icon may hide behind the `^` arrow next to the clock.

Your administrator chooses the folders to back up. KopiaUI shows them at its next refresh,
within 4 hours, or at once with its refresh button. If you click **New Snapshot** yourself,
you get access denied. This is expected: ask your administrator to add the folder.

A machine that sleeps or stays off takes no backup. A laptop backs up from anywhere it can
reach the server, at home too. Your administrator gets a mail when your machine has not backed
up for a few days, and you may get one first.

### Linux with GNOME

GNOME has no tray, so KopiaUI runs with no way to open it. Ubuntu ships the AppIndicator
extension that brings the tray back. On Fedora, Debian and other GNOME systems, install and
enable it:

```sh
sudo dnf install gnome-shell-extension-appindicator   # Fedora, Rocky
sudo apt install gnome-shell-extension-appindicator   # Debian
# log out and back in, GNOME Shell only sees new extensions in a new session
gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com
```

### macOS

macOS blocks apps from reading protected folders in the home directory (Mail, Messages,
Safari, parts of `~/Library`, and Desktop or Documents when iCloud syncs them) until they get
**Full Disk Access**. Without it, backups skip these folders or end with errors. Every backup
tool except Time Machine needs this permission.

1. Open System Settings, Privacy & Security, Full Disk Access, and enable **KopiaUI**.
2. Restart KopiaUI.
3. Add KopiaUI to System Settings, General, Login Items, so it starts at each login.

### Linux server

The Linux server script backs up your whole home directory with a systemd user timer,
`kopia-snapshot.timer`. It enables lingering, so the timer keeps running after you log out.
If the script cannot enable it, ask root to run `loginctl enable-linger <user>`. Check the
timer with:

```sh
systemctl --user list-timers kopia-snapshot.timer
```

## Leave out files

To leave out files or folders, put a `.kopiaignore` file in a backed up folder, or in any
folder below it. It holds one rule per line, in the gitignore syntax:

```
*.iso
Downloads/
/Videos/
```

`*.iso` skips every `.iso` file, `Downloads/` skips every folder named `Downloads`, and
`/Videos/` skips only the `Videos` folder at the top. The file applies to its folder and
everything inside. When your administrator backs up `C:\Users\anna\Documents`, the file goes
in that `Documents` folder, not in `C:\Users\anna`.

It only applies to the next backups. Files already saved stay in the older backups for a
while.

## Restore files

In KopiaUI, open **Snapshots**, pick a folder, then a date. **Restore** copies files back.
**Mount** opens the backup as a folder, so you can copy files from it with your file manager.

From the command line:

```sh
kopia snapshot list
kopia snapshot restore <snapshot id> /path/to/restore
```

## New computer

When your computer is replaced or reinstalled, ask your administrator for a new script.
Install KopiaUI, run the new script, and your old backups show up again in KopiaUI.
