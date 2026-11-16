//
// Copyright (C) 2026 Nethesis S.r.l.
// SPDX-License-Identifier: GPL-3.0-or-later
//

// The core keeps task output in Redis for hours. Actions that return a secret
// encrypt it for a key pair that lives only in this page.

const RSA = {
  name: "RSA-OAEP",
  modulusLength: 2048,
  publicExponent: new Uint8Array([1, 0, 1]),
  hash: "SHA-256",
};

function toBase64(buffer) {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)));
}

function fromBase64(text) {
  return Uint8Array.from(atob(text), (c) => c.charCodeAt(0));
}

export async function createSealKey() {
  const pair = await crypto.subtle.generateKey(RSA, false, [
    "encrypt",
    "decrypt",
  ]);
  const spki = await crypto.subtle.exportKey("spki", pair.publicKey);
  return { publicKey: toBase64(spki), privateKey: pair.privateKey };
}

export async function openSealed(result, privateKey) {
  if (!result.sealed) {
    return result;
  }
  const rawKey = await crypto.subtle.decrypt(
    { name: "RSA-OAEP" },
    privateKey,
    fromBase64(result.sealed.key)
  );
  const aesKey = await crypto.subtle.importKey(
    "raw",
    rawKey,
    "AES-GCM",
    false,
    ["decrypt"]
  );
  const data = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: fromBase64(result.sealed.iv) },
    aesKey,
    fromBase64(result.sealed.data)
  );
  return JSON.parse(new TextDecoder().decode(data));
}
