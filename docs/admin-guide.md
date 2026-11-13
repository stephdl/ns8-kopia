# Admin guide

This guide is for the NS8 administrator who runs the module and enrolls the machines. The
person who uses a machine has its own [user guide](user-guide.md). How the module works
inside is in [architecture](architecture.md).

The examples use the instance `kopia1`.

## Install

```sh
add-module ghcr.io/stephdl/kopia:latest 1
```

The output of the command returns the instance name, for example `kopia1`.

One instance serves one company: ACLs keep the machines apart inside one repository. Run
several instances on one node only to host several customers, each with its own repository,
password, disk and port.

## Pages of the module

**Status** shows the services, the repository disk, the server certificate, the last
integrity check and the machine states. A warning appears when the disk is 85 % full, when
the certificate expires within 30 days, and when the last integrity check failed or did not
finish.

**Clients** lists the machines with their last backup and their state. From there you add a
machine, reset its password, see its connection details, manage its folders, or remove it.

**Settings** holds the host, Let's Encrypt for the admin web UI, the client port and the admin
password.

**Policies** holds the global policy of every machine (schedule, retention, compression,
excludes) and the share of data read by the weekly integrity check.

**Alerts** holds the owner and admin thresholds, the recipients, the sender, the language,
and a test mail.

Each page saves only its own fields. Saving restarts the server only when the host, the port,
the image, a password or the certificate changed, since a restart cuts the running backups.

## First configuration

Fill in **Settings**, or from the command line send at least `host` and `admin_password`:

```sh
api-cli run module/kopia1/configure-module --data - <<'EOF'
{
  "host": "kopia.example.org",
  "lets_encrypt": true,
  "client_port": 51515,
  "admin_password": "Admin-pass-2026",
  "admin_recipients": ["it@example.org"]
}
EOF
```

Later calls send only the fields to change.

The repository is created at the first configuration. Its password is generated at install and
kept in the module backup, so a restore brings it back with the repository. Nobody needs to
type it. The secret to keep outside the server is the password of the cluster backup: without
it no module backup can be restored. The module backup holds the repository and its password
together, so anyone with the cluster backup password can read the backups of every machine.

You need the repository password only to open the repository without NS8, for example from a
copy of the volume. Read it on the node:

```sh
runagent -m kopia1 grep KOPIA_PASSWORD secrets/kopia.env
```

It never changes. If it leaks, install a new instance and enroll the machines again.

Choose the host and the client port before the first machine. Both are in the URL of every
enrolled machine, so the module refuses to change them while machines exist.

The web UI user is always `admin`. The Kopia web UI answers at `https://<host>/`.

### Network

Machines connect to the client port, 51515 by default, not to 443. The module opens it in
the NS8 firewall. If the server is behind NAT, forward that port on the router. The machines
only connect outbound, so open nothing on them. A laptop on a network that allows only 80 and
443 cannot back up there. It catches up later, and the late backup alert covers the gap.

### Fields

| Field | Page | Default | Allowed values |
| --- | --- | --- | --- |
| `host` | Settings | | a fully qualified name |
| `lets_encrypt` | Settings | `false` | for the admin web UI only |
| `client_port` | Settings | 51515, or the next free one | 1024 to 65535, free on the node, outside 20000 to 45000 |
| `admin_password` | Settings | | 12 to 64 characters, with an uppercase letter, a lowercase letter, a digit and a symbol among `.,_+:@%^=~-` |
| `snapshot_interval` | Policies | 4 | hours between snapshots: 0, 1, 2, 4, 6, 8, 12 or 24. 0 means manual only |
| `keep_latest`, `keep_hourly`, `keep_daily`, `keep_weekly`, `keep_monthly`, `keep_annual` | Policies | 10, 48, 14, 8, 12, 2 | 0 to 1000 |
| `compression` | Policies | `zstd` | Kopia compression names |
| `excludes` | Policies | caches, temp folders, trash, `node_modules`, Windows swap files | one gitignore rule per line |
| `verify_percent` | Policies | 10 | 0 to 100 |
| `owner_alert_hours` | Alerts | 48 | 1 to 8760 |
| `admin_alert_hours` | Alerts | 96 | 1 to 8760 |
| `admin_recipients` | Alerts | none | mail addresses |
| `alert_sender` | Alerts | `noreply@<host>` | a mail address |
| `alert_language` | Alerts | `en` | en, fr, it, de, es, pt, pt_BR, eu |

The full schema is in
[configure-module/validate-input.json](../imageroot/actions/configure-module/validate-input.json).

### Integrity check

The weekly integrity check runs on Sunday at 03:00. It always checks the index and that every
pack exists, then downloads and checks the share of data set on the Policies page. At 10 %
the whole repository is read again within a few months. At 0 % no data is read and silent
corruption goes unnoticed. A check stops after 6 days and 23 hours: the Status page then
shows it as not finished, with no error mail, and you should lower the share.

## Enroll a machine

### 1. Install the Kopia client

Follow the Kopia installation guide: <https://kopia.io/docs/installation/>. Use the same
version as the server when you can (0.23.1 today).

| System | Install | What the module script needs |
| --- | --- | --- |
| Windows | KopiaUI ([guide](https://kopia.io/docs/installation/#windows-gui-installation)) or `winget install -e --id Kopia.KopiaUI` | nothing: the script installs KopiaUI with winget when it is missing |
| Linux desktop | KopiaUI from the [APT or RPM repositories](https://kopia.io/docs/installation/#linux-installation-using-apt-debian-ubuntu) | KopiaUI, which schedules the snapshots. With the `kopia` command only, use the Linux server script |
| Linux server | `kopia` from the [APT or RPM repositories](https://kopia.io/docs/installation/#linux-installation-using-apt-debian-ubuntu) | the `kopia` command in the PATH, a systemd user session, and lingering (`loginctl enable-linger <user>` as root if the script cannot enable it) |
| macOS | KopiaUI ([guide](https://kopia.io/docs/installation/#macos-gui-installer)) | KopiaUI in `/Applications`, which schedules the snapshots |

KopiaUI and the CLI share the same config file, so KopiaUI shows a machine enrolled by the
script.

### 2. Create the machine account

On the **Clients** page, click **Add a machine**, and fill in:

- **User name** and **host name**: the Kopia identity of the machine, `user@host`. Lowercase
  letters, digits, dot, dash and underscore. Use one account per machine, for example
  `accounting@pc-accounting-01`.
- **Owner email** (optional): this person gets the first mail when the machine stops backing up.

The button first reads **Verify**. When the name still has snapshots from a removed machine,
a warning gives their count and dates, and the button becomes **Save**. Save to give them to
the new machine on purpose, or pick another name.

The page then shows the enrollment script, with three tabs: Windows (PowerShell), Linux and
macOS desktop (shell), and Linux server (shell, for a machine without KopiaUI). **Copy it
now**: it holds the password of the machine and is shown only once. Later, **Connection
details** shows the URL, the certificate fingerprint and the identity, without the password.
To get a script again, reset the password.

Never put the script in a GPO or in Intune in clear text. Anyone who reads it can read and
restore the backups of that machine.

### 3. Run the script on the machine

Send the script with the [user guide](user-guide.md), or run it yourself. It must run as the
user who owns the files, in that user's session. Not as administrator, root or SYSTEM: the
config and the password would land in another profile, and KopiaUI in the user session would
see nothing.

- Windows: open PowerShell as the user, paste the script and press Enter.
- Linux and macOS desktop, Linux server: save it as `enroll.sh` and run `sh enroll.sh`, then
  delete the file.

The script connects to `https://<host>:<client port>`, pins the module certificate
fingerprint, and stores the password in the OS keyring (or in the Kopia config folder on
Linux without a keyring).

On a desktop it takes no snapshot. Go to step 4.

On a Linux server it backs up the whole home directory. It adds a `kopia-snapshot.timer`
systemd user timer at the policy interval (none in manual mode), and enables lingering so it
keeps running after logout. The interval is written in the timer: after you change it on the
Policies page, reset the password of the server and run the new script.

Volume Shadow Copy on Windows needs administrator rights. The default script runs as the user
and backs up the user files. For a whole machine backup, enroll it in an elevated session as
a dedicated account instead.

### 4. Add the folders of a desktop

A desktop cannot pick its own folders: **New Snapshot** in KopiaUI fails with access denied,
because it writes a policy and a machine only reads its policies. You add them.

On the **Clients** page, **Folders** in the menu of the machine lists the folders it backs up
and the date of their last snapshot. To add one, type its absolute path as the machine sees
it, such as `/home/anna/Documents` or `C:\Users\anna\Documents`, and click **Open in Kopia**.
The Kopia web UI opens on the policy of that folder: log in as `admin` and click
**Save Policy**. Windows paths keep their backslashes.

KopiaUI on the machine sees the new folder at its next refresh, within 4 hours, or at once
with its refresh button. It then snapshots each folder at the policy interval while it runs.
To remove a folder, delete its policy in the Kopia web UI, opened with **Edit in Kopia**.

The module opens the policy editor by its URL because the Policies form of the Kopia web UI
rejects `user@host:/path` targets in Kopia 0.23.1 (kopia/kopia#5815).

Back up the folders that matter, such as a shared accounting folder, from a server, not from
a user machine. The user of a desktop can stop KopiaUI or exclude folders.

### 5. Check

The machine shows **Never seen** on the Clients page until its first snapshot, then **OK**.
The admin sees the snapshots of every machine in the Kopia web UI at `https://<host>/`.

## Exclude files and folders

An exclude is a rule that tells Kopia to skip some files or folders. During a snapshot Kopia
walks the folder, and when a name matches a rule it skips it, with everything inside when it is
a folder. Rules use the gitignore syntax, one rule per line:

- `*.iso` skips every `.iso` file, anywhere;
- `Downloads/` skips every folder named `Downloads`, at any level;
- `/Downloads/` skips only the `Downloads` folder at the top of the backed up folder;
- `**/.local/share/containers` skips this path at any depth.

There are two ways to exclude something.

1. **Every machine**: the **Policies** page of the module, field **Excluded patterns**. The
   field already holds the default rules: add your lines below them and keep them, since a
   line you remove is no longer excluded. In particular keep
   `repository.config.kopia-password`, the file where a Linux client stores its password. For
   example `**/.local/share/containers` skips the rootless Podman storage, which the user
   often cannot read and which would end each snapshot with a permission error.
2. **On the machine**: a `.kopiaignore` file in the backed up folder, or in any folder below
   it. It applies to its folder and everything inside, on top of the rules of the Policies
   page. For a machine that backs up `C:\Users\anna\Documents`, the file goes in that folder,
   not in the home folder above it. This is the only way the user of a machine can exclude
   something, since the machine cannot change its policies. The [user guide](user-guide.md#leave-out-files)
   explains it to them.

The Kopia policy editor of a folder, opened with **Edit in Kopia**, also has an
**Ignore Files** list under **Files**. Avoid it. As soon as a folder has its own list, Kopia
uses that list alone and drops every rule of the Policies page for this folder, defaults
included. If you still use it, copy into it every rule of the Policies page first, then add
yours. This is how Kopia merges policies, the more specific one wins.

**Ignore Well-Known Cache Directories** is on by default: Kopia skips any folder holding a
`CACHEDIR.TAG` file.

An exclude only applies to the next snapshots. Files already saved stay in the older snapshots
until the retention drops them.

## Manage machines

### Reinstall a machine or replace a leaked script

Click **Reset password** on the machine, run the new script on it, then delete the script. The
old password stops working at once. The identity does not change, so the machine finds its
old snapshots.

### Remove a machine

**Remove** deletes the account. By default its snapshots stay in the repository: a machine
added later with the same `user@host` sees and restores them, which is how a dead machine is
replaced, and so do its folders. Check **Also delete all its snapshots** to wipe the snapshots
and the folders instead. The machine cannot do it itself, and maintenance frees the space
within a day or two.

### Restore files

The user restores from KopiaUI or the `kopia` command, see the
[user guide](user-guide.md#restore-files). A machine only sees its own snapshots. The admin
sees every machine in the Kopia web UI at `https://<host>/`, user `admin`, and can restore
from there.

## Alerts

`kopia-check` runs every hour. A machine that never backed up counts from the day its
account was created. A desktop without folders backs up nothing, so it gets the late mails
too. One mail goes out when a threshold is crossed, never one per run.

| Mail | Subject (English) | Sent to | When |
| --- | --- | --- | --- |
| Owner late | `Backup late: <machine>` | owner email of the machine | last backup reaches the owner threshold (default 48 h) |
| Admin late | `Backup late: <machine> (<hours> h)` | admin recipients | last backup reaches the admin threshold (default 96 h) |
| Back to normal | `Backup back to normal: <machine>` | owner, plus admins if they were warned | a new backup brings the age under the owner threshold |
| Verification failed | `Backup verification failed on <host>` | admin recipients | the weekly integrity check finds errors |
| Test | `Kopia test mail from <host>` | the address typed on the Alerts page | the admin clicks "Send test mail" |

A machine that comes back from the admin level to the owner level gets no mail: it backed up
once, but it is still late.

Mails go through the cluster smarthost, in the language chosen on the Alerts page. Without a
smarthost no mail leaves, and the states stay visible on the Clients and Status pages.

## Backup, restore, clone and move

The module backup holds the configuration, the secrets and the `kopia-repository` volume, so
the history of every machine. Pick an off-site destination in the cluster backup, such as S3,
and run it at least once a day: a restore loses every snapshot taken since the last backup.
The Kopia packs never change once written, so each backup only sends the new ones. The
destination needs about the size of the repository.

The machines keep backing up while the cluster backup runs. Kopia maintenance is paused
during that time and resumes after the backup, or after 24 hours when a backup fails.

The backup does not protect against an attacker who is root on the node: restic needs to
delete in the destination to prune, so the same access can wipe it.

### Restore

Restore on the same or another node gives the same certificate, the same passwords and the
same repository. The machine accounts come back from their stored hashes. Point the host name
to the new node, and the machines reconnect with their old config and keep their history.

After the restore, the module walks every snapshot. A snapshot that ended while the backup
copied the repository can miss data in the restored copy. The check reports it on the Status
page and mails the admins.

A machine that was lost too gets enrolled again with the same `user@host`: reset its password
in Clients, run the new script, and restore its files from KopiaUI.

A backup taken before the repository was in the module backup restores an empty repository.
The machines then start a new history.

The restore keeps the client port. On a node where another instance holds it, the restored
instance stays stopped. Remove the other instance, save the settings of the restored one to
start it, then run the snapshot check by hand:

```sh
runagent -m kopia1 systemctl --user start kopia-verify-snapshots.service
```

### Clone and move

Clone and move copy the `kopia-repository` volume too, so the history is kept. A clone is a
full copy: same host, same client port, same certificate, same machine accounts. On another
node it starts at once. On the same node the source still holds the port and the route, so
the clone stays stopped. Remove the old instance, then save the settings of the clone to
start it. This is the way to move the repository to a bigger additional disk. The machines
keep working without any change. A move keeps everything.

## Uninstall

```sh
remove-module --no-preserve kopia1
```

This deletes the repository volume and every backup in it.

## Troubleshooting

**A machine stays Never seen.** A desktop has no folder yet: add one in **Folders**. Or
KopiaUI is not running on it: it must stay in the tray, and start at login. Or the machine
cannot reach the client port: check the firewall of its network, and the port forward when
NS8 is behind NAT. A machine that sleeps or stays off takes no snapshot either.

**KopiaUI says access denied on New Snapshot.** This is expected. The machine cannot create
policies. Add the folder from the Clients page.

**A machine is Unknown.** The Kopia server did not answer `list-clients`. Check the Status
page for a failed service.

**Snapshots end with permission errors.** A folder the user cannot read, often the rootless
Podman storage on Linux or a protected folder on macOS. Exclude it on the Policies page, or
on macOS give KopiaUI Full Disk Access (see the [user guide](user-guide.md#macos)).

**The integrity check did not finish.** It ran out of time. Lower the share of data on the
Policies page.

**The disk is full.** Delete `RESERVED-SPACE-delete-if-disk-full` at the top of the
`kopia-repository` volume to give Kopia room, then lower the retention or move the
repository to a bigger disk (see [Clone and move](#clone-and-move)). A full disk can damage a
filesystem repository.

**The instance is stopped after a restore or a clone.** Another instance on the node holds the
client port. See [Restore](#restore).

**Logs.** Open the System logs page of cluster-admin and filter on the instance. The state of
the services:

```sh
runagent -m kopia1 systemctl --user status kopia-server kopia-check.timer kopia-verify.timer
```
