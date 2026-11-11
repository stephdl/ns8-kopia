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

