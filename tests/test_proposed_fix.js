/**
 * Verification of proposed fix for static/cwallet_sync.js
 */
const assert = require('assert');

function parseDOMTextFixed(text, state = { lastSec: null, currentPhase: 'BETTING' }) {
    var isBattleText = /in\s*battle|battling|settling|battle\s*phase/i.test(text);

    var secMatch = text.match(/(\d{1,2})\s*s\b/i);
    var sec = secMatch ? parseInt(secMatch[1], 10) : null;

    var strikeMatch = text.match(/(?:Start|Strike|Open|Base|Price)[\s\:\$]*([\d,]+\.\d{2,4})/i);
    var p = strikeMatch ? parseFloat(strikeMatch[1].replace(/,/g, '')) : null;
    if (!p) {
        // Only match numbers with explicit decimals or currency sign >= 100, excluding sec
        var priceCandidates = text.match(/\$[\s]*[\d,]+(?:\.\d{2,4})?|[\d,]{3,}\.\d{2,4}/g);
        if (priceCandidates && priceCandidates.length > 0) {
            for (var cand of priceCandidates) {
                var clean = parseFloat(cand.replace(/[\$,]/g, ''));
                if (clean > 100 && clean !== sec) {
                    p = clean;
                    break;
                }
            }
        }
    }

    var currentPhase = state.currentPhase;
    var lastSec = state.lastSec;

    if (sec !== null) {
        // Disambiguation: sec > 5 can NEVER be battle (battle duration is strictly 5s)
        if (sec > 5) {
            currentPhase = 'BETTING';
        } else if (isBattleText) {
            currentPhase = 'BATTLE';
        } else if (sec <= 5) {
            // Jump transition: betting ends (lastSec <= 1) and battle countdown resets to 4-5s
            if (lastSec !== null && lastSec <= 1 && sec >= 4 && currentPhase === 'BETTING') {
                currentPhase = 'BATTLE';
            } else if (lastSec !== null && lastSec <= 1 && sec >= 4 && currentPhase === 'BATTLE') {
                currentPhase = 'BETTING';
            }
        }
        lastSec = sec;
    }

    var willSendPayload = (sec !== null && sec >= 0 && sec <= 60);

    return {
        isBattleText,
        sec,
        p,
        currentPhase,
        lastSec,
        willSendPayload
    };
}

console.log("=== VERIFYING PROPOSED FIX FOR cwallet_sync.js ===");

let state = { lastSec: null, currentPhase: 'BETTING' };
const seq = [15, 14, 10, 5, 2, 1, 0, 5, 4, 3, 2, 1, 0, 15, 14];
console.log("\n1. Sequential Transition Test:");
for (let s of seq) {
    let res = parseDOMTextFixed('Round ' + s + 's', state);
    console.log(`  sec=${s} -> phase=${res.currentPhase} (lastSec was ${state.lastSec})`);
    state.lastSec = res.lastSec;
    state.currentPhase = res.currentPhase;
}

// Assertions on sequence:
assert.strictEqual(parseDOMTextFixed("Round 0s", { lastSec: 1, currentPhase: 'BETTING' }).currentPhase, 'BETTING');
assert.strictEqual(parseDOMTextFixed("Round 5s", { lastSec: 0, currentPhase: 'BETTING' }).currentPhase, 'BATTLE');
assert.strictEqual(parseDOMTextFixed("Round 4s", { lastSec: 5, currentPhase: 'BATTLE' }).currentPhase, 'BATTLE');
assert.strictEqual(parseDOMTextFixed("Round 0s", { lastSec: 1, currentPhase: 'BATTLE' }).currentPhase, 'BATTLE');
assert.strictEqual(parseDOMTextFixed("Round 15s", { lastSec: 0, currentPhase: 'BATTLE' }).currentPhase, 'BETTING');

console.log("\n2. Simultaneous Battle text and Betting 12s:");
const simRes = parseDOMTextFixed("Status: In Battle (0/10) | Betting Phase 12s Strike $65000.00");
console.log("  Result:", simRes.currentPhase, "sec:", simRes.sec);
assert.strictEqual(simRes.currentPhase, 'BETTING'); // sec > 5 overrides isBattleText!

console.log("\n3. Non-numeric strike 'Strike: pending':");
const pendRes = parseDOMTextFixed("Time left: 10s Strike: pending");
console.log("  Result price:", pendRes.p, "sec:", pendRes.sec);
assert.strictEqual(pendRes.p, null); // Does not capture 10 as price!

console.log("\n4. Price without label '15s $67890.12':");
const fallRes = parseDOMTextFixed("15s $67890.12");
console.log("  Result price:", fallRes.p);
assert.strictEqual(fallRes.p, 67890.12);

console.log("\nALL PROPOSED FIX TESTS PASSED!");
