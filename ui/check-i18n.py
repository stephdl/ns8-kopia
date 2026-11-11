#!/usr/bin/env python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

# Check that every language file has the keys, the {placeholders} and the plural forms of en.

import json
import re
import sys
from pathlib import Path

root = Path(__file__).parent / "public" / "i18n"


def flatten(node, prefix=""):
    for key, value in node.items():
        name = prefix + key
        if isinstance(value, dict):
            yield from flatten(value, name + ".")
        else:
            yield name, value


def load(lang):
    return dict(flatten(json.loads((root / lang / "translation.json").read_text(encoding="utf-8"))))


reference = load("en")
errors = []
for path in sorted(root.glob("*/translation.json")):
    lang = path.parent.name
    if lang == "en":
        continue
    data = load(lang)
    for key in sorted(reference.keys() - data.keys()):
        errors.append(f"{lang}: missing key {key}")
    for key in sorted(data.keys() - reference.keys()):
        errors.append(f"{lang}: extra key {key}")
    for key in sorted(reference.keys() & data.keys()):
        if sorted(re.findall(r"\{\w+\}", reference[key])) != sorted(re.findall(r"\{\w+\}", data[key])):
            errors.append(f"{lang}: placeholders differ in {key}")
        if reference[key].count(" | ") != data[key].count(" | "):
            errors.append(f"{lang}: plural forms differ in {key}")
        if "—" in data[key]:
            errors.append(f"{lang}: em dash in {key}")
        if not data[key].strip():
            errors.append(f"{lang}: empty text in {key}")

for line in errors:
    print(line)
print(f"{len(reference)} keys in en, {len(errors)} problem(s)")
sys.exit(1 if errors else 0)
