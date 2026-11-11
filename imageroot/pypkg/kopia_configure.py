#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""Rebuild the configure-module request from an environment, for restore and clone."""

import kopia_module as km


def request_from_env(env):
    data = {
        # An instance saved before its first configuration has no host yet
        "host": env.get("TRAEFIK_HOST", ""),
        "lets_encrypt": env.get("TRAEFIK_LETS_ENCRYPT") == "True",
        "client_port": int(env.get("CLIENT_PORT", km.DEFAULT_PORT)),
    }
    data.update(km.read_settings(env))
    return data


def ensure_free_port(data):
    """Move to the next free port when the saved one is taken on this node.

    It goes to the environment before configure-module runs: the lock refuses a port change
    while machines exist, and an unchanged port skips the free port check.
    """
    import os
    import sys
    import agent
    port = km.free_port(agent.redis_connect(), data["client_port"])
    if port != data["client_port"]:
        print(agent.SD_WARNING + f"client port {data['client_port']} is taken on this node, using {port}", file=sys.stderr)
        agent.set_env("CLIENT_PORT", str(port))
        agent.dump_env()
        os.environ["CLIENT_PORT"] = str(port)
        data["client_port"] = port
    return data
