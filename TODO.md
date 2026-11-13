# TODO

Ideas kept for later. Nothing here is planned or promised.

## Kopia replica on S3

### The idea

Keep the repository on the local disk, as today. Add an optional copy of it on an S3 bucket, made by `kopia repository sync-to s3`. The copy is a full Kopia repository. Kopia can open it from any computer, without NS8.

The goal is the 3-2-1-1-0 rule: 3 copies, 2 media, 1 off site, 1 immutable, 0 errors on restore checks. The cluster backup to S3 already gives 3-2-1: the data on the machines, the local repository, and the restic backup. The replica would add the immutable copy and a way to read the backups without NS8.

### How it could work

The Settings page gets an optional replica section: endpoint, bucket, prefix, region, access key, secret key, schedule. The keys go to `state/secrets`.

A systemd timer, like `kopia-check`, runs at night:

```sh
kopia snapshot create /state --override-source=ns8@kopia1:/state
kopia repository sync-to s3 --bucket=... --prefix=... --endpoint=... \
  --access-key=... --secret-access-key=... --delete --parallel=4
```

The first command stores the module state in the repository itself: secrets, certificates, `clients.json`. Kopia encrypts it like any other snapshot. The machines cannot see it, because their ACLs only cover their own `user@host`. So the replica carries everything needed to rebuild the server.

The sync should not run during the maintenance. It can reuse the pause that `module-dump-state` already uses.

`get-health` shows the date and the result of the last sync. A failed or old sync sends a mail with the existing alerts.

A periodic check reads part of the replica, for example `kopia snapshot verify --verify-files-percent=...` while connected to the bucket. A failure sends a mail.

### Immutability

The bucket does the job, not the module. Turn on versioning and Object Lock in COMPLIANCE mode, with a default retention of 30 days for example. Add a lifecycle rule that expires old versions after that delay.

With this, a delete or an overwrite only adds a marker. The old versions stay locked, even for someone who stole the S3 keys from the server. Kopia reads a past state of the bucket:

```sh
kopia repository connect s3 ... --point-in-time=2026-11-01T00:00:00Z
```

This gives back the history that a plain mirror lacks.

### Using the replica

Machines never use the replica. They only talk to the Kopia server with their own account, and only that server enforces the ACLs. Opening the replica needs the repository password and the S3 keys, which give access to every machine. So they never go to a machine.

The admin uses it in two cases.

To give a file back while the server is down, connect to the bucket from any computer, then `kopia snapshot list --all` and `kopia restore`, or `kopia mount`.

To rebuild the server, install the module on a new NS8 and run a new `restore-from-replica` action. It connects to the bucket, restores `ns8@kopia1:/state` into `/state`, runs `sync-to filesystem --path=/repo/data`, then starts the server. With the same host and certificate, the machines reconnect without a new enrollment.

A read only Kopia server on the replica would also work, since the accounts live in the repository. I leave it out: it has another certificate, and the next `sync-to --delete` would erase anything written there.

### For

- Reads the backups from any computer, without NS8 and without restoring a whole volume first. A file comes back in minutes.
- With Object Lock, the copy survives an attacker who controls the server and holds the S3 keys.
- `--point-in-time` gives a dated history of the whole repository.
- The sync is incremental at the Kopia blob level, so the nightly upload stays small.
- It runs in the existing container. No new port, no change for the machines.

### Against

- The cluster backup already covers 3-2-1, with history and a one click restore of the whole module. For most installs the replica adds little.
- The repository password opens the replica and the saved state. It lives in `state/secrets` today, inside what it protects. The admin must keep it outside the server, so the UI must show it once with a clear warning. If it is lost, the replica is useless.
- Without versioning and Object Lock on the bucket, the replica is a plain mirror. A corruption or a delete reaches S3 at the next sync.
- Kopia does not promise a consistent copy when the sync runs during writes. The next run catches up, but a replica taken at a bad moment can miss the last snapshots.
- The first sync uploads the whole repository, which can take days on a large one.
- New code to keep working: UI, timer, restore action, alerts, docs, and a CI test against an S3 service.
- I have not checked how the restic prune of the cluster backup behaves on a bucket with Object Lock. That matters if someone wants the immutable copy without the replica.

### Decision

Not now. Point admins to the cluster backup on S3 for 3-2-1. Build the replica when someone needs an immutable copy or fast restores without NS8.
