/*
 * codec.js — submission-code encoder for the WebR escape rooms.
 *
 * WHAT THE CODE CARRIES
 *   A short alphanumeric string (e.g. "7QF2-K93X") that encodes, for one
 *   student's run of one scenario:
 *     - a header byte: version (high nibble) + scenario id (low nibble)
 *     - one byte per step/node: chosen answer index (low 5 bits, 0-31)
 *                          + attempts taken (high 3 bits, 0-7; 0 = not attempted)
 *     - a checksum byte over the payload
 *   The payload is XOR-scrambled with a keystream derived from a shared
 *   secret AND the student's id, then Crockford base32 encoded.
 *
 * WHY IT IS SHAPED THIS WAY
 *   - Because the keystream depends on the student id, two students with the
 *     same answer path get different-looking codes, and a code decoded with
 *     the WRONG student id fails its checksum (so shared codes are detectable).
 *   - The checksum catches typos on submission and wrong-student decodes.
 *
 * HONEST LIMITS
 *   The secret lives in this file, which ships to the browser. This is
 *   OBFUSCATION, not security: a determined student who reads the JS could
 *   forge a code. It is a speed bump appropriate for low-stakes practice.
 *
 * The R decoder in ../decoder/decode_codes.R mirrors every function below.
 * If you change the arithmetic here, change it there too.
 */
(function () {
  "use strict";

  var CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"; // no I L O U
  var TWO32 = 4294967296; // 2^32

  // Rolling polynomial hash, 32-bit, kept inside 2^53 so plain doubles are exact.
  function hash32(str) {
    var h = 2166136261;
    for (var i = 0; i < str.length; i++) {
      h = (h * 31 + str.charCodeAt(i)) % TWO32;
    }
    return h;
  }

  function hashBytes(bytes) {
    var h = 2166136261;
    for (var i = 0; i < bytes.length; i++) {
      h = (h * 31 + bytes[i]) % TWO32;
    }
    return h;
  }

  // Deterministic keystream: an LCG seeded by hash(secret + "|" + studentId).
  // Each output byte is a middle slice of the 32-bit state.
  function keystream(secret, studentId, n) {
    var seed = hash32(secret + "|" + String(studentId).trim().toLowerCase());
    var state = seed;
    var out = [];
    for (var i = 0; i < n; i++) {
      state = (1664525 * state + 1013904223) % TWO32;
      out.push(Math.floor(state / 65536) % 256);
    }
    return out;
  }

  function crockfordEncode(bytes) {
    // `value` is kept to at most `bits` (<8) after each extraction so it never
    // exceeds ~2^12 — this keeps the arithmetic exact in JS doubles no matter
    // how long the code is, matching R/Python for arbitrarily many steps.
    var bits = 0, value = 0, output = "";
    for (var i = 0; i < bytes.length; i++) {
      value = (value * 256) + bytes[i];
      bits += 8;
      while (bits >= 5) {
        bits -= 5;
        output += CROCKFORD[Math.floor(value / Math.pow(2, bits)) % 32];
        value = value % Math.pow(2, bits); // drop the consumed high bits
      }
    }
    if (bits > 0) {
      output += CROCKFORD[(value * Math.pow(2, 5 - bits)) % 32];
    }
    return output;
  }

  /*
   * steps: array of { answer: <int 0-31>, attempts: <int >=1> }
   * returns a display code like "7QF2-K93X" (dash purely cosmetic).
   */
  function encode(opts) {
    var version = opts.version & 0x0f;
    var scenarioId = opts.scenarioId & 0x0f;
    var payload = [(version << 4) | scenarioId];
    opts.steps.forEach(function (s) {
      var ans = s.answer & 0x1f;               // 5 bits
      // 3 bits; 0 = "not attempted" (a hub-and-spoke node the student skipped
      // under an N-of-M gate). Solved/resolved nodes carry attempts >= 1.
      var att = Math.min(Math.max(s.attempts, 0), 7) & 0x07;
      payload.push((att << 5) | ans);
    });
    var chk = hashBytes(payload) % 256;
    var full = payload.concat([chk]);
    var ks = keystream(opts.secret, opts.studentId, full.length);
    var scrambled = full.map(function (b, i) { return b ^ ks[i]; });
    var raw = crockfordEncode(scrambled);
    // group into blocks of 4 for legibility
    return raw.replace(/(.{4})(?=.)/g, "$1-");
  }

  window.EscapeCodec = { encode: encode };
})();
