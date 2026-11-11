#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""Shared helpers of the Kopia module. Every path is relative to the module state directory."""

import base64
import hashlib
import hmac
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

SECRETS_DIR = "secrets"
KOPIA_ENV = "secrets/kopia.env"
CLIENT_SECRETS = "secrets/clients.json"
CLIENTS = "clients.json"
CERT = "certs/client.pem"
CERT_KEY = "certs/client-key.pem"
CONTAINER = "kopia-server"
IMAGE_ENV = "KOPIA_IMAGE"
SERVER_USER = "server"
SERVER_HOST = "kopia"
ADMIN_USER = "admin"
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


# --- secrets -----------------------------------------------------------------

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


# --- machine accounts ----------------------------------------------------------

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


def load_client_secrets():
    try:
        with open(CLIENT_SECRETS) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_client_secrets(values):
    _write_private(CLIENT_SECRETS, json.dumps(values, indent=2))


def client_name(username, hostname):
    return f"{username}@{hostname}"


# --- Kopia password hashes ------------------------------------------------------

def _scrypt(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P,
                          maxmem=128 * 1024 * 1024, dklen=HASH_LEN)


def hash_password(password):
    """Encode a hash the way `kopia server user add --user-password-hash` expects it."""
    salt = os.urandom(SALT_LEN)
    payload = salt + _scrypt(password, salt)
    doc = {"passwordHashVersion": SCRYPT_HASH_VERSION, "passwordHash": base64.b64encode(payload).decode()}
    return base64.b64encode(json.dumps(doc, separators=(",", ":")).encode()).decode()


def check_password(password, profile):
    """True when the password matches a profile of `kopia server user list --json`."""
    if profile.get("passwordHashVersion", SCRYPT_HASH_VERSION) != SCRYPT_HASH_VERSION:
        return False
    try:
        payload = base64.b64decode(profile.get("passwordHash", ""))
    except ValueError:
        return False
    if len(payload) != SALT_LEN + HASH_LEN:
        return False
    return hmac.compare_digest(payload[SALT_LEN:], _scrypt(password, payload[:SALT_LEN]))


# --- certificate -------------------------------------------------------------------

def cert_fingerprint(path=CERT):
    out = subprocess.run(["openssl", "x509", "-in", path, "-noout", "-fingerprint", "-sha256"],
                         check=True, capture_output=True, text=True).stdout
    return out.strip().split("=", 1)[1].replace(":", "").lower()


def cert_expiry(path=CERT):
    out = subprocess.run(["openssl", "x509", "-in", path, "-noout", "-enddate"],
                         check=True, capture_output=True, text=True).stdout
    return out.strip().split("=", 1)[1]


# --- Kopia commands ------------------------------------------------------------------

def kopia(args, stdin=None, script=None, check=True, timeout=600):
    """Run kopia inside the server container with the current secrets.

    Secrets reach the process through --env-file and stdin, never through the command line.
    With script, args is ignored and the shell snippet runs instead, reading stdin.
    """
    cmd = ["podman", "exec", "-i", "--env-file", KOPIA_ENV, CONTAINER]
    cmd += ["sh", "-c", script] if script else ["kopia"] + args
    proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        log(proc.stderr.strip())
        raise RuntimeError(f"kopia {' '.join(args) if not script else 'script'} failed ({proc.returncode})")
    return proc


def kopia_json(args):
    return json.loads(kopia(args + ["--json"]).stdout or "null")


def server_refresh():
    """Make the server read new users and ACLs now instead of at the next index refresh."""
    port = os.environ.get("CLIENT_PORT", str(DEFAULT_PORT))
    script = (f'KOPIA_SERVER_USERNAME={CONTROL_USER} KOPIA_SERVER_PASSWORD="$KOPIA_SERVER_CONTROL_PASSWORD" '
              f'kopia server refresh --address=https://127.0.0.1:{port} '
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


# --- node ports -------------------------------------------------------------------------

def port_listening(port):
    out = subprocess.run(["ss", "-Htln", f"sport = :{port}"], capture_output=True, text=True).stdout
    return bool(out.strip())


def port_used_by_other_module(rdb, port, module_id, node_id):
    for key in rdb.scan_iter("module/*/environment"):
        other = key.split("/")[1]
        if other == module_id:
            continue
        env = rdb.hgetall(key)
        if env.get("NODE_ID") == str(node_id) and env.get("CLIENT_PORT") == str(port):
            return other
    return None


# --- volume -------------------------------------------------------------------------------

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


# --- settings -------------------------------------------------------------------------------

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
    "excludes": ("EXCLUDES", [
        ".cache", "Cache", "Caches", "cache2", "Temp", "tmp", "*.tmp", "~$*",
        "$RECYCLE.BIN", ".Trash-*", "node_modules", "Thumbs.db", ".DS_Store",
        "hiberfil.sys", "pagefile.sys", "swapfile.sys",
    ], list),
    "owner_alert_hours": ("OWNER_ALERT_HOURS", 48, int),
    "admin_alert_hours": ("ADMIN_ALERT_HOURS", 96, int),
    "admin_recipients": ("ADMIN_RECIPIENTS", [], list),
    "alert_sender": ("ALERT_SENDER", "", str),
    "alert_language": ("ALERT_LANGUAGE", "en", str),
    "disk_alert_percent": ("DISK_ALERT_PERCENT", 85, int),
}


def _encode(value, kind):
    return json.dumps(value) if kind is list else str(value)


def _decode(raw, default, kind):
    if raw is None or raw == "":
        return default if kind is not list or raw is None else []
    try:
        return json.loads(raw) if kind is list else kind(raw)
    except ValueError:
        return default


SETTINGS_DEFAULTS = {env: _encode(default, kind) for env, default, kind in SETTINGS.values()}


def read_settings(env=None):
    env = os.environ if env is None else env
    return {field: _decode(env.get(var), default, kind) for field, (var, default, kind) in SETTINGS.items()}


def settings_to_env(data):
    return {var: _encode(data[field], kind) for field, (var, _, kind) in SETTINGS.items() if field in data}


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
    args += [f"--remove-ignore={pattern}" for pattern in current_ignore if pattern not in s["excludes"]]
    args += [f"--add-ignore={pattern}" for pattern in s["excludes"] if pattern not in current_ignore]
    return args


# --- machine status --------------------------------------------------------------------------

def parse_time(value):
    from datetime import datetime
    # Kopia writes nanoseconds, Python reads microseconds
    value = re.sub(r"(\.\d{6})\d+", r"\1", value).replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def last_snapshots():
    """Return {user@host: newest end time} of the complete snapshots."""
    last = {}
    for snap in kopia_json(["snapshot", "list", "--all"]) or []:
        if snap.get("incomplete"):
            continue
        src = snap["source"]
        name = client_name(src["userName"], src["host"])
        end = parse_time(snap["endTime"])
        if name not in last or end > last[name]:
            last[name] = end
    return last


def clients_status(settings=None):
    """Merge the machine list with the newest snapshot of each machine."""
    from datetime import datetime, timezone
    settings = settings or read_settings()
    now = datetime.now(timezone.utc)
    last = last_snapshots()
    result = []
    for client in load_clients():
        end = last.get(client["name"])
        if end is None:
            state, age = "never_seen", None
        else:
            age = (now - end).total_seconds() / 3600
            if age >= settings["admin_alert_hours"]:
                state = "late_admin"
            elif age >= settings["owner_alert_hours"]:
                state = "late"
            else:
                state = "ok"
        result.append(dict(client, last_backup=end.isoformat() if end else None,
                           age_hours=round(age, 1) if age is not None else None, state=state))
    return result


# --- mail -------------------------------------------------------------------------------------

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
    # The pod reaches the node loopback at 10.0.2.2, but this code runs on the node itself
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
    port = start
    while port_listening(port) or port_used_by_other_module(rdb, port, os.environ["MODULE_ID"], os.environ["NODE_ID"]):
        port += 1
    return port
