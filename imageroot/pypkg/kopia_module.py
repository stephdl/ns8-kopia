#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""Shared helpers of the Kopia module. Every path is relative to the module state directory."""

import base64
import hashlib
import json
import os
import re
import secrets as pysecrets
import socket
import ssl
import string
import subprocess
import sys
import urllib.error
import urllib.request

KOPIA_ENV = "secrets/kopia.env"
# Only scrypt hashes: the password of a machine is shown once, when it is created or reset
CLIENT_HASHES = "secrets/client-hashes.json"
# Clear passwords kept by the first versions, converted on first read
OLD_CLIENT_SECRETS = "secrets/clients.json"
CLIENTS = "clients.json"
CERT = "certs/client.pem"
CONTAINER = "kopia-server"
CONTROL_USER = "server-control"
DEFAULT_PORT = 51515
# Ports handed out by the node port allocator, see node.ports_manager
ALLOCATOR_RANGE = (20000, 45000)

PASSWORD_ALLOWED = re.compile(r"^[A-Za-z0-9.,_+:@%^=~-]+$")
NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9._-]{0,62}[a-z0-9])?$")

# Same scrypt settings as Kopia internal/crypto and internal/user, so the module can compute and check hashes
SCRYPT_N, SCRYPT_R, SCRYPT_P = 65536, 8, 1
HASH_LEN = SALT_LEN = 32
SCRYPT_HASH_VERSION = 1


def log(*args):
    print(*args, file=sys.stderr)



def _write_private(path, text):
    os.makedirs(os.path.dirname(path) or ".", mode=0o700, exist_ok=True)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def read_env(path=KOPIA_ENV):
    values = {}
    try:
        with open(path) as f:
            for line in f:
                if "=" in line:
                    key, value = line.rstrip("\n").split("=", 1)
                    values[key] = value
    except FileNotFoundError:
        pass
    return values


def write_env(values, path=KOPIA_ENV):
    _write_private(path, "".join(f"{k}={v}\n" for k, v in values.items() if v))


def generate_password(length=24):
    # Letters and digits only: the value goes into shell and PowerShell scripts without quoting trouble
    alphabet = string.ascii_letters + string.digits
    return "".join(pysecrets.choice(alphabet) for _ in range(length))


def password_error(value):
    """Return the name of the broken rule, or None. The UI checks the same rules."""
    if not 12 <= len(value) <= 64:
        return "password_length"
    if not PASSWORD_ALLOWED.match(value):
        return "password_characters"
    for pattern in ("[A-Z]", "[a-z]", "[0-9]", "[.,_+:@%^=~-]"):
        if not re.search(pattern, value):
            return "password_classes"
    return None



class clients_lock:
    """Serialize the actions that change clients.json and client-hashes.json."""

    def __enter__(self):
        import fcntl
        self.fd = open(".clients.lock", "w")
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        self.fd.close()


def load_clients():
    try:
        with open(CLIENTS) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_clients(clients):
    tmp = CLIENTS + ".tmp"
    with open(tmp, "w") as f:
        json.dump(sorted(clients, key=lambda c: c["name"]), f, indent=2)
    os.replace(tmp, CLIENTS)


def load_client_hashes():
    try:
        with open(CLIENT_HASHES) as f:
            hashes = json.load(f)
    except FileNotFoundError:
        hashes = {}
    if os.path.exists(OLD_CLIENT_SECRETS):
        with open(OLD_CLIENT_SECRETS) as f:
            for name, password in json.load(f).items():
                hashes.setdefault(name, hash_password(password))
        save_client_hashes(hashes)
        os.remove(OLD_CLIENT_SECRETS)
    return hashes


def save_client_hashes(values):
    _write_private(CLIENT_HASHES, json.dumps(values, indent=2))


def set_user_hash(name, encoded, exists):
    """Create or update a Kopia account. The hash goes through stdin, never on the command line."""
    verb = "set" if exists else "add"
    # name matches NAME_PATTERN on both sides of the @, so it needs no shell quoting
    kopia([], stdin=encoded + "\n", script=f'read -r h; {KOPIA} server user {verb} {name} --user-password-hash="$h"')


def set_client_password(name, users=None):
    """Give the account a new random password, store only its hash and return the password.

    The caller holds clients_lock.
    """
    password = generate_password()
    encoded = hash_password(password)
    if users is None:
        users = {u["username"] for u in kopia_json(["server", "user", "list"]) or []}
    # Account first: a failure leaves the stored hash matching the account
    set_user_hash(name, encoded, exists=name in users)
    hashes = load_client_hashes()
    hashes[name] = encoded
    save_client_hashes(hashes)
    return password


def client_name(username, hostname):
    return f"{username}@{hostname}"



def _scrypt(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P,
                          maxmem=128 * 1024 * 1024, dklen=HASH_LEN)


def hash_password(password):
    """Encode a hash the way `kopia server user add --user-password-hash` expects it."""
    salt = os.urandom(SALT_LEN)
    payload = salt + _scrypt(password, salt)
    doc = {"passwordHashVersion": SCRYPT_HASH_VERSION, "passwordHash": base64.b64encode(payload).decode()}
    return base64.b64encode(json.dumps(doc, separators=(",", ":")).encode()).decode()


def hash_matches(encoded, profile):
    """True when an encoded hash of hash_password() is the one of a `server user list --json` profile."""
    try:
        doc = json.loads(base64.b64decode(encoded))
    except ValueError:
        return False
    return (doc.get("passwordHashVersion") == profile.get("passwordHashVersion", SCRYPT_HASH_VERSION)
            and doc.get("passwordHash") == profile.get("passwordHash"))





def cert_fingerprint(path=CERT):
    out = subprocess.run(["openssl", "x509", "-in", path, "-noout", "-fingerprint", "-sha256"],
                         check=True, capture_output=True, text=True).stdout
    return out.strip().split("=", 1)[1].replace(":", "").lower()


def cert_expiry(path=CERT):
    out = subprocess.run(["openssl", "x509", "-in", path, "-noout", "-enddate"],
                         check=True, capture_output=True, text=True).stdout
    return out.strip().split("=", 1)[1]



# The journal gets the console output: the debug log files only filled the container
KOPIA = "kopia --disable-file-logging --disable-content-log"


def kopia(args, stdin=None, script=None, check=True, timeout=600):
    """Run kopia inside the server container with the current secrets.

    Secrets reach the process through --env-file and stdin, never through the command line.
    With script, args is ignored and the shell snippet runs instead, reading stdin.
    """
    cmd = ["podman", "exec", "-i", "--env-file", KOPIA_ENV, CONTAINER]
    cmd += ["sh", "-c", script] if script else KOPIA.split() + args
    proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        log(proc.stderr.strip())
        # Only the subcommand: later arguments can hold a password hash
        raise RuntimeError(f"kopia {' '.join(args[:3]) if not script else 'script'} failed ({proc.returncode})")
    return proc


# Present while the cluster backup copies the repository, holds the time the pause started
MAINTENANCE_PAUSED = "maintenance-paused"


def set_maintenance(enabled):
    """Turn the quick and full maintenance of the repository on or off.

    The setting lives in the repository, so a repository restored from a backup comes back paused.
    """
    flag = "true" if enabled else "false"
    kopia(["maintenance", "set", f"--enable-quick={flag}", f"--enable-full={flag}"])


def kopia_json(args):
    return json.loads(kopia(args + ["--json"]).stdout or "null")


# Policies of the machines and their folders, copied out of the repository by each cluster backup
POLICIES_DUMP = "policies.json"
# Left by restore-module, removed by the first apply that imported the dump
POLICIES_PENDING = "policies-pending"
# Restic pattern added to state-exclude.conf when the repository stays out of the cluster backup
REPOSITORY_EXCLUDE = "volumes/kopia-repository/data"


def dump_policies():
    """Save every policy but the global one, which configure-module rebuilds from the settings."""
    policies = json.loads(kopia(["policy", "export"]).stdout or "{}")
    policies.pop("(global)", None)
    tmp = POLICIES_DUMP + ".tmp"
    with open(tmp, "w") as f:
        json.dump(policies, f, indent=2)
    os.replace(tmp, POLICIES_DUMP)
    return len(policies)


def restore_policies():
    """Import the saved policies the repository lacks: all of them after a backup without the repository."""
    try:
        with open(POLICIES_DUMP) as f:
            saved = json.load(f)
    except FileNotFoundError:
        return 0
    present = set(json.loads(kopia(["policy", "export"]).stdout or "{}"))
    missing = {target: policy for target, policy in saved.items() if target not in present}
    if missing:
        kopia(["policy", "import"], stdin=json.dumps(missing))
    return len(missing)


def write_state_exclude(backup_repository, path=None):
    """Add or drop the repository pattern in the exclude list the core reads after module-dump-state.

    update-module brings back the shipped file, and the next backup writes the line again."""
    path = path or os.path.join(os.environ["AGENT_INSTALL_DIR"], "etc", "state-exclude.conf")
    with open(path) as f:
        lines = [line for line in f.read().splitlines() if line.strip() != REPOSITORY_EXCLUDE]
    if not backup_repository:
        lines.append(REPOSITORY_EXCLUDE)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, path)


def server_refresh():
    """Make the server read new users, ACLs and policies now instead of at the next index refresh."""
    port = os.environ.get("CLIENT_PORT", str(DEFAULT_PORT))
    script = (f'KOPIA_SERVER_USERNAME={CONTROL_USER} KOPIA_SERVER_PASSWORD="$KOPIA_SERVER_CONTROL_PASSWORD" '
              f'{KOPIA} server refresh --address=https://127.0.0.1:{port} '
              f'--server-cert-fingerprint={cert_fingerprint()}')
    kopia([], script=script)


def server_status(port=None, timeout=5):
    """Return the HTTP status of the server root, or None when it does not answer."""
    port = port or os.environ.get("CLIENT_PORT", str(DEFAULT_PORT))
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(NoRedirect, urllib.request.HTTPSHandler(context=ctx))
    try:
        return opener.open(f"https://127.0.0.1:{port}/", timeout=timeout).status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, socket.timeout, ConnectionError, ssl.SSLError):
        return None


def wait_server(attempts=60):
    import time
    for _ in range(attempts):
        # Without credentials a running server answers 401
        if server_status() == 401:
            return True
        time.sleep(2)
    return False



def port_listening(port):
    out = subprocess.run(["ss", "-Htln", f"sport = :{port}"], capture_output=True, text=True).stdout
    return bool(out.strip())


def ports_taken(rdb, module_id, node_id):
    """Return {port: module} for the client ports of the other modules on this node."""
    taken = {}
    for key in rdb.scan_iter("module/*/environment"):
        other = key.split("/")[1]
        if other == module_id:
            continue
        env_node, env_port = rdb.hmget(key, "NODE_ID", "CLIENT_PORT")
        if env_node == str(node_id) and env_port and env_port.isdigit():
            taken[int(env_port)] = other
    return taken


def port_used_by_other_module(rdb, port, module_id, node_id):
    return ports_taken(rdb, module_id, node_id).get(int(port))



def own_route():
    """Return the route of this instance, {} when it has none, None when Traefik does not answer.

    agent.get_route() returns {} in both cases, so a slow Traefik would look like a missing route.
    """
    import agent
    response = agent.tasks.run(agent_id=agent.resolve_agent_id("traefik@node"), action="get-route",
                               data={"instance": os.environ["MODULE_ID"]},
                               extra={"isNotificationHidden": True})
    if response["exit_code"] != 0:
        return None
    return response["output"] or {}


def volume_path(name="kopia-repository"):
    out = subprocess.run(["podman", "volume", "inspect", name, "--format", "{{.Mountpoint}}"],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def disk_usage(name="kopia-repository"):
    path = volume_path(name)
    if not path:
        return None
    st = os.statvfs(path)
    total = st.f_blocks * st.f_frsize
    free = st.f_bavail * st.f_frsize
    used = total - st.f_bfree * st.f_frsize
    return {"total": total, "used": used, "free": free,
            "percent": round(used * 100 / total, 1) if total else 0}



# Every update pushes these to every instance, even after the admin saved the Policies page
DEFAULT_EXCLUDES = [
    ".cache", "Cache", "Caches", "cache2", "Temp", "tmp", "*.tmp", "~$*",
    "$RECYCLE.BIN", ".Trash-*", "node_modules", "Thumbs.db", ".DS_Store",
    "hiberfil.sys", "pagefile.sys", "swapfile.sys",
    # Windows and running apps lock these during a session, so Kopia cannot read them
    # without VSS, which needs admin rights. Kopia matches case, hence the brackets.
    "[nN][tT][uU][sS][eE][rR].[dD][aA][tT]*", "[uU][sS][rR][cC][lL][aA][sS][sS].[dD][aA][tT]*",
    "**/AppData/Local/Microsoft/Windows/WebCache/",
    "**/AppData/Local/Microsoft/Windows/WebCacheLock.dat",
    "**/AppData/Local/Packages/*/Settings/", "**/AppData/Local/Packages/*/SystemAppData/",
    "**/AppData/Local/Packages/**/EBWebView/", "**/AppData/Local/Comms/UnistoreDB/",
    "**/AppData/Roaming/kopia-ui/",
    # Image layers of rootless containers belong to other user IDs, so the user cannot read
    # them. Volumes stay in the backup: they hold user data.
    "**/.local/share/containers/storage/overlay*/", "**/.local/share/containers/storage/vfs*/",
    "**/.local/share/docker/overlay2/", "**/.local/share/docker/vfs/",
    # Flatpak apps put their cache there, out of reach of the .cache rule
    "**/.var/app/*/cache/",
    # The client keeps its own password there
    "repository.config.kopia-password",
]

# configure-module field: (environment variable, default, kind)
SETTINGS = {
    "snapshot_interval": ("SNAPSHOT_INTERVAL", 4, int),
    "keep_latest": ("KEEP_LATEST", 10, int),
    "keep_hourly": ("KEEP_HOURLY", 48, int),
    "keep_daily": ("KEEP_DAILY", 14, int),
    "keep_weekly": ("KEEP_WEEKLY", 8, int),
    "keep_monthly": ("KEEP_MONTHLY", 12, int),
    "keep_annual": ("KEEP_ANNUAL", 2, int),
    "compression": ("COMPRESSION", "zstd", str),
    # Only the patterns the admin adds: DEFAULT_EXCLUDES always apply on top
    "excludes": ("EXCLUDES", [], list),
    "owner_alert_hours": ("OWNER_ALERT_HOURS", 48, int),
    "admin_alert_hours": ("ADMIN_ALERT_HOURS", 96, int),
    "admin_recipients": ("ADMIN_RECIPIENTS", [], list),
    "alert_sender": ("ALERT_SENDER", "", str),
    "alert_language": ("ALERT_LANGUAGE", "en", str),
    "verify_percent": ("VERIFY_PERCENT", 10, int),
    "backup_repository": ("BACKUP_REPOSITORY", True, bool),
}


def _encode(value, kind):
    return json.dumps(value) if kind is list else str(value)


def _decode(raw, default, kind):
    if raw is None or raw == "":
        return default if kind is not list or raw is None else []
    if kind is bool:
        # bool("False") is true
        return raw == "True"
    try:
        return json.loads(raw) if kind is list else kind(raw)
    except ValueError:
        return default


SETTINGS_DEFAULTS = {env: _encode(default, kind) for env, default, kind in SETTINGS.values()}


def configure_request():
    """Read the configure-module request. A page that saves only its own fields keeps the saved host."""
    data = json.load(sys.stdin)
    data.setdefault("host", os.environ.get("TRAEFIK_HOST", ""))
    return data


def extra_excludes(patterns):
    """Drop the built-in patterns: a list saved before they were forced holds them too."""
    return [pattern for pattern in patterns if pattern not in DEFAULT_EXCLUDES]


def read_settings(env=None):
    env = os.environ if env is None else env
    settings = {field: _decode(env.get(var), default, kind) for field, (var, default, kind) in SETTINGS.items()}
    settings["excludes"] = extra_excludes(settings["excludes"])
    return settings


def settings_to_env(data):
    if "excludes" in data:
        data = dict(data, excludes=extra_excludes(data["excludes"]))
    return {var: _encode(data[field], kind) for field, (var, _, kind) in SETTINGS.items() if field in data}


def effective_excludes(settings):
    return DEFAULT_EXCLUDES + settings["excludes"]


def alert_sender(settings=None):
    settings = settings or read_settings()
    return settings["alert_sender"] or f"noreply@{os.environ.get('TRAEFIK_HOST') or socket.getfqdn()}"


def global_policy_args(settings=None, current_ignore=()):
    """current_ignore is the ignore list stored now: Kopia drops --add-ignore when --clear-ignore is given."""
    s = settings or read_settings()
    args = ["policy", "set", "--global",
            f"--snapshot-interval={s['snapshot_interval']}h" if s["snapshot_interval"] else "--manual",
            f"--keep-latest={s['keep_latest']}", f"--keep-hourly={s['keep_hourly']}",
            f"--keep-daily={s['keep_daily']}", f"--keep-weekly={s['keep_weekly']}",
            f"--keep-monthly={s['keep_monthly']}", f"--keep-annual={s['keep_annual']}",
            f"--compression={s['compression']}"]
    excludes = effective_excludes(s)
    args += [f"--remove-ignore={pattern}" for pattern in current_ignore if pattern not in excludes]
    args += [f"--add-ignore={pattern}" for pattern in excludes if pattern not in current_ignore]
    return args



def parse_time(value):
    from datetime import datetime
    # Kopia writes nanoseconds, Python reads microseconds
    value = re.sub(r"(\.\d{6})\d+", r"\1", value).replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def folder_key(path):
    """Compare folder paths the way a machine reports them: no trailing separator, Windows drive
    letter and path case ignored, since Windows paths are case-insensitive."""
    if re.match(r"^[A-Za-z]:\\", path) or path.startswith("\\\\"):
        return path.rstrip("\\").lower() if len(path) > 3 else path.lower()
    return path.rstrip("/") or "/"


def machine_snapshots(name):
    """Return the snapshot manifests of every source of a machine identity, incomplete ones too."""
    return [snap for snap in kopia_json(["snapshot", "list", "--all", "--incomplete"]) or []
            if client_name(snap["source"]["userName"], snap["source"]["host"]) == name]


def machine_policies(name):
    """Return the policies defined for a machine identity, its own user@host one included."""
    return [pol for pol in kopia_json(["policy", "list"]) or []
            if client_name(pol["target"]["userName"], pol["target"]["host"]) == name]


# About 200 bytes each: 1000 errors keep the task output near 200 KB
MAX_LISTED_ERRORS = 1000


def snapshot_errors(snap):
    """Return (count, ignored, [{path, error}]) of the files and folders a snapshot could not read.
    Kopia lists the errors a policy ignores among the others, with nothing to tell them apart,
    so the count comes from the stats and the list may hold the ignored ones too."""
    summ = (snap.get("rootEntry") or {}).get("summ") or {}
    stats = snap.get("stats") or {}
    errors = [{"path": e.get("path", ""), "error": e.get("error", "")} for e in summ.get("errors") or []]
    count = stats.get("errorCount", summ.get("numFailed", 0))
    ignored = stats.get("ignoredErrorCount", summ.get("numIgnoredErrors", 0))
    return count, ignored, errors[:MAX_LISTED_ERRORS]


def snapshot_size(snap):
    """Return the bytes of the files a snapshot holds, before deduplication and compression."""
    summ = (snap.get("rootEntry") or {}).get("summ") or {}
    return (snap.get("stats") or {}).get("totalSize", summ.get("size"))


def newest_snapshots(snapshots):
    """Return {path: newest complete snapshot} of a list of snapshot manifests."""
    newest = {}
    for snap in snapshots:
        if snap.get("incomplete"):
            continue
        path = snap["source"]["path"]
        if path not in newest or parse_time(snap["endTime"]) > parse_time(newest[path]["endTime"]):
            newest[path] = snap
    return newest


def folder_disabled(policy):
    """True when disable-client-folder switched the folder to manual scheduling: the machine keeps
    the snapshots but takes no new one."""
    return bool((policy.get("scheduling") or {}).get("manual"))


def disabled_folders(policies):
    return {pol["target"]["path"] for pol in policies if pol["target"]["path"] and folder_disabled(pol)}


def by_machine(manifests, key):
    """Group snapshot or policy manifests by user@host, from one kopia call for every machine."""
    grouped = {}
    for item in manifests or []:
        grouped.setdefault(client_name(item[key]["userName"], item[key]["host"]), []).append(item)
    return grouped


def lateness(age_hours, settings):
    if age_hours >= settings["admin_alert_hours"]:
        return "late_admin"
    if age_hours >= settings["owner_alert_hours"]:
        return "late"
    return "ok"


def clients_status(settings=None):
    """Merge the machine list with the newest snapshot of each folder of each machine.
    error_count sums the read errors and total_size the bytes of the newest snapshot
    of each folder still enabled.
    last_error_backup is the end time of the newest of those snapshots."""
    from datetime import datetime, timezone
    settings = settings or read_settings()
    now = datetime.now(timezone.utc)
    snapshots = by_machine(kopia_json(["snapshot", "list", "--all"]), "source")
    try:
        policies = by_machine(kopia_json(["policy", "list"]), "target")
    except (RuntimeError, OSError, ValueError) as ex:
        # Only the error count needs the policies: keep the lateness, count every folder
        log(f"cannot read policies: {ex}")
        policies = {}
    result = []
    for client in load_clients():
        newest = newest_snapshots(snapshots.get(client["name"], []))
        disabled = disabled_folders(policies.get(client["name"], []))
        ends = [parse_time(snap["endTime"]) for snap in newest.values()]
        end = max(ends) if ends else None
        if end is None:
            state, age = "never_seen", None
        else:
            age = (now - end).total_seconds() / 3600
            state = lateness(age, settings)
        enabled = [snap for path, snap in newest.items() if path not in disabled]
        sizes = [size for size in map(snapshot_size, enabled) if size is not None]
        failing = [(snap, snapshot_errors(snap)[0]) for snap in enabled]
        failing = [(snap, count) for snap, count in failing if count]
        error_ends = [parse_time(snap["endTime"]) for snap, _ in failing]
        result.append(dict(client, last_backup=end.isoformat() if end else None,
                           age_hours=round(age, 1) if age is not None else None, state=state,
                           total_size=sum(sizes) if sizes else None,
                           error_count=sum(count for _, count in failing),
                           last_error_backup=max(error_ends).isoformat() if error_ends else None))
    return result



def send_mail(rdb, recipients, subject, body, sender=None):
    import smtplib
    from email.message import EmailMessage
    import agent
    conf = agent.get_smarthost_settings(rdb)
    if not conf["enabled"]:
        raise RuntimeError("smarthost_disabled")
    msg = EmailMessage()
    msg["From"] = sender or alert_sender()
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)
    ctx = ssl.create_default_context()
    if not conf["tls_verify"]:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    host = conf["host"]
    if conf["encrypt_smtp"] == "tls":
        smtp = smtplib.SMTP_SSL(host, conf["port"], context=ctx, timeout=30)
    else:
        smtp = smtplib.SMTP(host, conf["port"], timeout=30)
        if conf["encrypt_smtp"] == "starttls":
            smtp.starttls(context=ctx)
    with smtp:
        if conf["username"]:
            smtp.login(conf["username"], conf["password"])
        smtp.send_message(msg)


def free_port(rdb, start=DEFAULT_PORT):
    taken = ports_taken(rdb, os.environ["MODULE_ID"], os.environ["NODE_ID"])
    port = start
    while port in taken or port_listening(port):
        port += 1
    return port
