//
// Copyright (C) 2026 Nethesis S.r.l.
// SPDX-License-Identifier: GPL-3.0-or-later
//

// Same rules as the backend: 12 to 64 characters, these characters only, one of each class
const ALLOWED = /^[A-Za-z0-9.,_+:@%^=~-]+$/;
const SYMBOLS = ".,_+:@%^=~-";
const UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ";
const LOWER = "abcdefghijkmnopqrstuvwxyz";
const DIGITS = "23456789";

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

function randomInt(max) {
  // Rejection sampling keeps every character equally likely
  const limit = 256 - (256 % max);
  const buffer = new Uint8Array(1);
  do {
    window.crypto.getRandomValues(buffer);
  } while (buffer[0] >= limit);
  return buffer[0] % max;
}

function pick(chars) {
  return chars[randomInt(chars.length)];
}

export function generatePassword(length = 24) {
  const all = UPPER + LOWER + DIGITS + SYMBOLS;
  const chars = [pick(UPPER), pick(LOWER), pick(DIGITS), pick(SYMBOLS)];
  while (chars.length < length) {
    chars.push(pick(all));
  }
  // Fisher-Yates shuffle, so the first four characters are not predictable
  for (let i = chars.length - 1; i > 0; i--) {
    const j = randomInt(i + 1);
    [chars[i], chars[j]] = [chars[j], chars[i]];
  }
  return chars.join("");
}
