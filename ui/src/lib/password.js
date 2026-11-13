//
// Copyright (C) 2026 Nethesis S.r.l.
// SPDX-License-Identifier: GPL-3.0-or-later
//

// Same rules as the backend: 12 to 64 characters, these characters only, one of each class
const ALLOWED = /^[A-Za-z0-9.,_+:@%^=~-]+$/;

export function passwordError(value) {
  if (value.length < 12 || value.length > 64) {
    return "settings.password_length";
  }
  if (!ALLOWED.test(value)) {
    return "settings.password_characters";
  }
  if (
    !/[A-Z]/.test(value) ||
    !/[a-z]/.test(value) ||
    !/[0-9]/.test(value) ||
    !/[.,_+:@%^=~-]/.test(value)
  ) {
    return "settings.password_classes";
  }
  return "";
}
